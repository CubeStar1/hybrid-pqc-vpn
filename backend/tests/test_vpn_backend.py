from __future__ import annotations

from pathlib import Path

import pytest

from hybrid_vpn.agent import AgentService
from hybrid_vpn.config import AgentConfig
from hybrid_vpn.schemas import ConnectRequest
from hybrid_vpn.tunnel import ClientRouteManager, GatewayNetworkManager, TunnelManager


class DummyThread:
    def __init__(self) -> None:
        self.join_calls = 0

    def join(self, timeout: float | None = None) -> None:
        del timeout
        self.join_calls += 1


class DummyTun:
    def __init__(self) -> None:
        self.name = "hyb0"
        self.mtu = 1280
        self._open = False
        self.close_calls = 0

    def open(self) -> str:
        self._open = True
        return self.name

    def close(self) -> None:
        self._open = False
        self.close_calls += 1

    @property
    def is_open(self) -> bool:
        return self._open


class DummyUdp:
    def __init__(self) -> None:
        self.local_port = 4434
        self._sock = object()
        self.close_calls = 0

    def bind(self) -> None:
        self._sock = object()

    def close(self) -> None:
        self.close_calls += 1
        self._sock = None


def test_tunnel_manager_stop_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = TunnelManager(
        "hyb0",
        "10.42.0.2",
        24,
        1280,
        b"\x00" * 32,
        b"\x01" * 32,
        4434,
        ("127.0.0.1", 4433),
    )
    manager.tun = DummyTun()
    manager.tun._open = True
    manager.udp = DummyUdp()
    manager._running = True
    manager._threads = [DummyThread(), DummyThread()]

    cleanup_calls: list[str] = []
    monkeypatch.setattr("hybrid_vpn.tunnel.cleanup_tun_interface", lambda name: cleanup_calls.append(name))

    manager.stop()
    manager.stop()

    assert manager.tun.close_calls == 1
    assert manager.udp.close_calls == 1
    assert cleanup_calls == ["hyb0"]


def test_tunnel_manager_start_cleans_stale_interface(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = TunnelManager(
        "hyb0",
        "10.42.0.2",
        24,
        1280,
        b"\x00" * 32,
        b"\x01" * 32,
        4434,
        ("127.0.0.1", 4433),
    )
    manager.tun = DummyTun()
    manager.udp = DummyUdp()

    cleanup_calls: list[str] = []
    monkeypatch.setattr("hybrid_vpn.tunnel.interface_exists", lambda name: name == "hyb0")
    monkeypatch.setattr("hybrid_vpn.tunnel.cleanup_tun_interface", lambda name: cleanup_calls.append(name))
    monkeypatch.setattr("hybrid_vpn.tunnel.configure_tun", lambda *args, **kwargs: None)

    class FakeThread:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs

        def start(self) -> None:
            return None

        def join(self, timeout: float | None = None) -> None:
            del timeout

    monkeypatch.setattr("hybrid_vpn.tunnel.threading.Thread", FakeThread)

    manager.start()

    assert cleanup_calls == ["hyb0"]
    assert manager.is_running is True


def test_client_route_manager_preserves_gateway_host_route(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    class Result:
        def __init__(self, stdout: str = "[]", returncode: int = 0) -> None:
            self.stdout = stdout
            self.returncode = returncode

    def fake_run_command(args: list[str], check: bool = True) -> Result:
        del check
        calls.append(args)
        if args == ["ip", "-j", "route", "show", "default"]:
            return Result('[{"dev":"eth0","gateway":"192.168.1.1","metric":100}]')
        if args == ["ip", "-j", "route", "get", "198.51.100.10"]:
            return Result('[{"dev":"eth0","gateway":"192.168.1.1","prefsrc":"192.168.1.50"}]')
        return Result()

    monkeypatch.setattr("hybrid_vpn.tunnel.run_command", fake_run_command)
    manager = ClientRouteManager("hyb0", "198.51.100.10")

    manager.apply_full_tunnel()
    manager.restore()

    assert ["ip", "route", "replace", "198.51.100.10/32", "via", "192.168.1.1", "dev", "eth0", "src", "192.168.1.50"] in calls
    assert ["ip", "route", "replace", "default", "dev", "hyb0"] in calls
    assert ["ip", "route", "replace", "default", "via", "192.168.1.1", "dev", "eth0", "metric", "100"] in calls


def test_gateway_network_manager_is_idempotent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    installed_rules: set[tuple[str, ...]] = set()

    class Result:
        def __init__(self, returncode: int = 1) -> None:
            self.returncode = returncode
            self.stdout = ""

    def fake_run_command(args: list[str], check: bool = True) -> Result:
        del check
        calls.append(args)
        if "-C" in args:
            rule = tuple(arg for arg in args if arg != "-C")
            return Result(returncode=0 if rule in installed_rules else 1)
        if "-A" in args:
            installed_rules.add(tuple(arg for arg in args if arg != "-A"))
        if "-D" in args:
            installed_rules.discard(tuple(arg for arg in args if arg != "-D"))
        return Result(returncode=0)

    monkeypatch.setattr("hybrid_vpn.tunnel.run_command", fake_run_command)

    ip_forward = tmp_path / "ip_forward"
    ip_forward.write_text("0\n", encoding="utf-8")

    manager = GatewayNetworkManager("hyb-gw0", "10.42.0.0/24", "eth0")
    manager._ip_forward_path = ip_forward

    manager.apply()
    manager.apply()
    manager.teardown()

    add_calls = [call for call in calls if "-A" in call]
    delete_calls = [call for call in calls if "-D" in call]
    assert len(add_calls) == 3
    assert len(delete_calls) == 3
    assert ip_forward.read_text(encoding="utf-8").strip() == "0"


def test_agent_connect_rolls_back_when_route_setup_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    config = AgentConfig(
        gateway_url="http://gateway.test",
        gateway_host="198.51.100.10",
        gateway_port=4433,
    )
    agent = AgentService(config)
    request = ConnectRequest(profile_id="lab-gateway", username="demo", password="demo-vpn-2026")

    class FakeResponse:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def json(self) -> dict:
            return self._payload

    stop_calls = 0
    start_calls = 0

    def fake_post(url: str, json: dict, timeout: float) -> FakeResponse:
        del timeout
        nonlocal stop_calls, start_calls
        if url.endswith("/auth"):
            return FakeResponse({"authenticated": True})
        if url.endswith("/handshake"):
            return FakeResponse(
                {
                    "x25519_public_hex": "11" * 32,
                    "mlkem_ciphertext_hex": None,
                    "ecdsa_signature_hex": "22",
                    "ecdsa_public_key_der_hex": "33",
                    "transcript_hash_hex": "44" * 32,
                }
            )
        if url.endswith("/session/start"):
            start_calls += 1
            return FakeResponse({"accepted": True, "message": "ok", "tunnel": {"gateway_nat_active": True}})
        if url.endswith("/session/stop"):
            stop_calls += 1
            return FakeResponse({"accepted": True, "message": json["reason"]})
        raise AssertionError(url)

    class FakeHandshakeClient:
        def create_hello(self):
            class Hello:
                suite = "suite"
                x25519_public = b"\x01" * 32
                mlkem_public = None

            return Hello()

        def finish(self, hello, server_hello):
            del hello, server_hello

            class Secrets:
                client_key = b"\x00" * 32
                server_key = b"\x01" * 32

            return Secrets()

    class FakeTunnelManager:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs
            self.is_running = False
            self.stats = {"packets_sent": 0, "packets_recv": 0, "bytes_sent": 0, "bytes_recv": 0}

        def start(self) -> None:
            self.is_running = True

        def stop(self) -> None:
            self.is_running = False

    class FailingRouteManager:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs
            self.is_active = False
            self.restore_called = False

        def apply_full_tunnel(self) -> None:
            raise RuntimeError("route setup failed")

        def restore(self) -> None:
            self.restore_called = True

    monkeypatch.setattr("hybrid_vpn.agent.IS_LINUX", True)
    monkeypatch.setattr("hybrid_vpn.agent.httpx.post", fake_post)
    monkeypatch.setattr("hybrid_vpn.agent.HandshakeClient", FakeHandshakeClient)
    monkeypatch.setattr("hybrid_vpn.agent.TunnelManager", FakeTunnelManager)
    monkeypatch.setattr("hybrid_vpn.agent.ClientRouteManager", FailingRouteManager)

    response = agent.connect(request, gateway_url=config.gateway_url)

    assert response.accepted is False
    assert "Tunnel creation failed" in response.message
    assert start_calls == 1
    assert stop_calls >= 1


def test_agent_reconnect_replaces_existing_session(monkeypatch: pytest.MonkeyPatch) -> None:
    config = AgentConfig(
        gateway_url="http://gateway.test",
        gateway_host="198.51.100.10",
        gateway_port=4433,
    )
    agent = AgentService(config)
    request = ConnectRequest(profile_id="lab-gateway", username="demo", password="demo-vpn-2026")

    class FakeResponse:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def json(self) -> dict:
            return self._payload

    start_calls = 0
    stop_calls = 0

    def fake_post(url: str, json: dict, timeout: float) -> FakeResponse:
        del timeout
        nonlocal start_calls, stop_calls
        if url.endswith("/auth"):
            return FakeResponse({"authenticated": True})
        if url.endswith("/handshake"):
            return FakeResponse(
                {
                    "x25519_public_hex": "11" * 32,
                    "mlkem_ciphertext_hex": None,
                    "ecdsa_signature_hex": "22",
                    "ecdsa_public_key_der_hex": "33",
                    "transcript_hash_hex": "44" * 32,
                }
            )
        if url.endswith("/session/start"):
            start_calls += 1
            return FakeResponse({"accepted": True, "message": "ok", "tunnel": {"gateway_nat_active": True}})
        if url.endswith("/session/stop"):
            stop_calls += 1
            return FakeResponse({"accepted": True, "message": json["reason"]})
        raise AssertionError(url)

    class FakeHandshakeClient:
        def create_hello(self):
            class Hello:
                suite = "suite"
                x25519_public = b"\x01" * 32
                mlkem_public = None

            return Hello()

        def finish(self, hello, server_hello):
            del hello, server_hello

            class Secrets:
                client_key = b"\x00" * 32
                server_key = b"\x01" * 32

            return Secrets()

    class FakeTunnelManager:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs
            self.is_running = False
            self.stats = {"packets_sent": 0, "packets_recv": 0, "bytes_sent": 0, "bytes_recv": 0}

        def start(self) -> None:
            self.is_running = True

        def stop(self) -> None:
            self.is_running = False

    class FakeRouteManager:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs
            self.is_active = False

        def apply_full_tunnel(self) -> None:
            self.is_active = True

        def restore(self) -> None:
            self.is_active = False

    monkeypatch.setattr("hybrid_vpn.agent.IS_LINUX", True)
    monkeypatch.setattr("hybrid_vpn.agent.httpx.post", fake_post)
    monkeypatch.setattr("hybrid_vpn.agent.HandshakeClient", FakeHandshakeClient)
    monkeypatch.setattr("hybrid_vpn.agent.TunnelManager", FakeTunnelManager)
    monkeypatch.setattr("hybrid_vpn.agent.ClientRouteManager", FakeRouteManager)

    first = agent.connect(request, gateway_url=config.gateway_url)
    second = agent.connect(request, gateway_url=config.gateway_url)

    assert first.accepted is True
    assert second.accepted is True
    assert start_calls == 2
    assert stop_calls >= 2
