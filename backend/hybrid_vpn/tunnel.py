"""Linux TUN device management and encrypted UDP tunnel transport.

Phase 2: UDP framing with AES-256-GCM encryption and sequence-number replay protection.
Phase 3: TUN creation via /dev/net/tun, IP/route management via pyroute2.

All Linux-specific operations are guarded so the module can be imported on any OS;
calling the actual tunnel functions on non-Linux raises a clear RuntimeError.
"""

from __future__ import annotations

import logging
import os
import platform
import json
import subprocess
import socket
import struct
import threading
from dataclasses import dataclass, field
from pathlib import Path

from .crypto.classical import aes_gcm_decrypt, aes_gcm_encrypt

logger = logging.getLogger(__name__)

IS_LINUX = platform.system() == "Linux"

# ioctl constants for TUN device creation (Linux only)
TUNSETIFF = 0x400454CA
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

# Packet frame layout: [4-byte sequence][encrypted payload + 16-byte GCM tag]
SEQ_SIZE = 4
MAX_PACKET = 2048


def _require_linux(operation: str) -> None:
    if not IS_LINUX:
        raise RuntimeError(f"{operation} requires Linux (current: {platform.system()})")


# ── TUN device ───────────────────────────────────────────────────────


@dataclass
class TunDevice:
    """Manages a Linux TUN network interface."""

    name: str = "hyb0"
    mtu: int = 1280
    _fd: int | None = field(default=None, init=False, repr=False)

    def open(self) -> str:
        """Create the TUN device. Returns the actual interface name."""
        _require_linux("TUN device creation")
        import fcntl

        self._fd = os.open("/dev/net/tun", os.O_RDWR)
        ifr = struct.pack("16sH", self.name.encode(), IFF_TUN | IFF_NO_PI)
        result = fcntl.ioctl(self._fd, TUNSETIFF, ifr)
        self.name = result[:16].strip(b"\x00").decode()
        logger.info("TUN device %s opened (fd=%d)", self.name, self._fd)
        return self.name

    def close(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            logger.info("TUN device %s closed", self.name)
            self._fd = None

    def read(self, size: int = MAX_PACKET) -> bytes:
        if self._fd is None:
            raise RuntimeError("TUN device not open")
        return os.read(self._fd, size)

    def write(self, data: bytes) -> int:
        if self._fd is None:
            raise RuntimeError("TUN device not open")
        return os.write(self._fd, data)

    @property
    def is_open(self) -> bool:
        return self._fd is not None


# ── Interface configuration (pyroute2) ───────────────────────────────


def configure_tun(name: str, address: str, prefixlen: int, mtu: int) -> None:
    """Assign IP address, set MTU, and bring the TUN interface up."""
    _require_linux("TUN configuration")
    from pyroute2 import IPRoute

    with IPRoute() as ipr:
        idx = ipr.link_lookup(ifname=name)
        if not idx:
            raise RuntimeError(f"Interface {name} not found")
        idx = idx[0]
        ipr.link("set", index=idx, mtu=mtu)
        ipr.addr("add", index=idx, address=address, prefixlen=prefixlen)
        ipr.link("set", index=idx, state="up")
    logger.info("Configured %s: %s/%d mtu=%d UP", name, address, prefixlen, mtu)


def interface_exists(name: str) -> bool:
    _require_linux("Interface lookup")
    from pyroute2 import IPRoute

    with IPRoute() as ipr:
        return bool(ipr.link_lookup(ifname=name))


def cleanup_tun_interface(name: str) -> None:
    """Delete a TUN interface if it still exists."""
    _require_linux("TUN teardown")
    from pyroute2 import IPRoute

    with IPRoute() as ipr:
        idx = ipr.link_lookup(ifname=name)
        if idx:
            index = idx[0]
            try:
                ipr.addr("flush", index=index)
            except Exception:
                logger.debug("Address flush failed for %s", name, exc_info=True)
            try:
                ipr.link("set", index=index, state="down")
            except Exception:
                logger.debug("Link down failed for %s", name, exc_info=True)
            try:
                ipr.link("del", index=index)
            except Exception:
                logger.debug("Link delete failed for %s", name, exc_info=True)
    logger.info("Interface %s cleaned up", name)


def run_command(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    _require_linux("Command execution")
    return subprocess.run(args, check=check, capture_output=True, text=True)


def _parse_json_command(args: list[str]) -> list[dict]:
    result = run_command(args)
    try:
        payload = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse JSON from {' '.join(args)}: {exc}") from exc
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected JSON payload from {' '.join(args)}")
    return payload


@dataclass
class DefaultRouteRecord:
    dev: str
    gateway: str | None = None
    prefsrc: str | None = None
    metric: int | None = None


@dataclass
class HostRouteRecord:
    dev: str
    gateway: str | None = None
    prefsrc: str | None = None


class ClientRouteManager:
    """Captures and restores the client's routing state for a full-tunnel session."""

    def __init__(self, tun_name: str, gateway_host: str) -> None:
        self.tun_name = tun_name
        self.gateway_host = gateway_host
        self._saved_defaults: list[DefaultRouteRecord] = []
        self._gateway_route: HostRouteRecord | None = None
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def apply_full_tunnel(self) -> None:
        _require_linux("Client route management")
        if self._active:
            return

        default_routes = _parse_json_command(["ip", "-j", "route", "show", "default"])
        if not default_routes:
            raise RuntimeError("No default route found to preserve before enabling the VPN")

        self._saved_defaults = [
            DefaultRouteRecord(
                dev=route["dev"],
                gateway=route.get("gateway"),
                prefsrc=route.get("prefsrc"),
                metric=route.get("metric"),
            )
            for route in default_routes
            if route.get("dev")
        ]

        gateway_route = _parse_json_command(["ip", "-j", "route", "get", self.gateway_host])
        if not gateway_route:
            raise RuntimeError(f"Could not resolve a route to gateway host {self.gateway_host}")
        resolved = gateway_route[0]
        dev = resolved.get("dev")
        if not dev:
            raise RuntimeError(f"Gateway route for {self.gateway_host} did not include an outbound device")
        self._gateway_route = HostRouteRecord(
            dev=dev,
            gateway=resolved.get("gateway"),
            prefsrc=resolved.get("prefsrc"),
        )

        host_route = ["ip", "route", "replace", f"{self.gateway_host}/32"]
        if self._gateway_route.gateway:
            host_route.extend(["via", self._gateway_route.gateway])
        host_route.extend(["dev", self._gateway_route.dev])
        if self._gateway_route.prefsrc:
            host_route.extend(["src", self._gateway_route.prefsrc])
        run_command(host_route)
        run_command(["ip", "route", "replace", "default", "dev", self.tun_name])
        self._active = True
        logger.info("Full-tunnel route override enabled via %s", self.tun_name)

    def restore(self) -> None:
        _require_linux("Client route restore")
        if not self._active:
            return

        try:
            run_command(["ip", "route", "del", "default", "dev", self.tun_name], check=False)
            for route in self._saved_defaults:
                restore_cmd = ["ip", "route", "replace", "default"]
                if route.gateway:
                    restore_cmd.extend(["via", route.gateway])
                restore_cmd.extend(["dev", route.dev])
                if route.prefsrc:
                    restore_cmd.extend(["src", route.prefsrc])
                if route.metric is not None:
                    restore_cmd.extend(["metric", str(route.metric)])
                run_command(restore_cmd)
            run_command(["ip", "route", "del", f"{self.gateway_host}/32"], check=False)
        finally:
            self._saved_defaults = []
            self._gateway_route = None
            self._active = False
            logger.info("Full-tunnel route override removed")


class GatewayNetworkManager:
    """Manages gateway forwarding/NAT state for a single tunnel subnet."""

    def __init__(self, tun_name: str, tunnel_cidr: str, uplink_iface: str) -> None:
        self.tun_name = tun_name
        self.tunnel_cidr = tunnel_cidr
        self.uplink_iface = uplink_iface
        self._active = False
        self._ip_forward_path = Path("/proc/sys/net/ipv4/ip_forward")
        self._previous_ip_forward: str | None = None

    @property
    def is_active(self) -> bool:
        return self._active

    def apply(self) -> None:
        _require_linux("Gateway network setup")
        if self._active:
            return

        self._previous_ip_forward = self._ip_forward_path.read_text(encoding="utf-8").strip()
        if self._previous_ip_forward != "1":
            self._ip_forward_path.write_text("1\n", encoding="utf-8")

        self._ensure_iptables_rule(
            ["-A", "FORWARD", "-i", self.tun_name, "-o", self.uplink_iface, "-j", "ACCEPT"],
        )
        self._ensure_iptables_rule(
            [
                "-A",
                "FORWARD",
                "-i",
                self.uplink_iface,
                "-o",
                self.tun_name,
                "-m",
                "state",
                "--state",
                "RELATED,ESTABLISHED",
                "-j",
                "ACCEPT",
            ],
        )
        self._ensure_iptables_rule(
            ["-t", "nat", "-A", "POSTROUTING", "-s", self.tunnel_cidr, "-o", self.uplink_iface, "-j", "MASQUERADE"],
        )
        self._active = True
        logger.info("Gateway forwarding/NAT enabled on %s", self.uplink_iface)

    def teardown(self) -> None:
        _require_linux("Gateway network teardown")
        if not self._active:
            return

        try:
            self._delete_iptables_rule(
                ["-t", "nat", "-D", "POSTROUTING", "-s", self.tunnel_cidr, "-o", self.uplink_iface, "-j", "MASQUERADE"],
            )
            self._delete_iptables_rule(
                [
                    "-D",
                    "FORWARD",
                    "-i",
                    self.uplink_iface,
                    "-o",
                    self.tun_name,
                    "-m",
                    "state",
                    "--state",
                    "RELATED,ESTABLISHED",
                    "-j",
                    "ACCEPT",
                ],
            )
            self._delete_iptables_rule(
                ["-D", "FORWARD", "-i", self.tun_name, "-o", self.uplink_iface, "-j", "ACCEPT"],
            )
            if self._previous_ip_forward is not None and self._previous_ip_forward != "1":
                self._ip_forward_path.write_text(f"{self._previous_ip_forward}\n", encoding="utf-8")
        finally:
            self._active = False
            logger.info("Gateway forwarding/NAT removed")

    def _ensure_iptables_rule(self, rule_args: list[str]) -> None:
        check_args = self._rule_with_check_flag(rule_args)
        result = run_command(check_args, check=False)
        if result.returncode != 0:
            run_command(["iptables", *rule_args])

    def _delete_iptables_rule(self, rule_args: list[str]) -> None:
        check_args = self._rule_with_check_flag(rule_args)
        result = run_command(check_args, check=False)
        if result.returncode == 0:
            run_command(["iptables", *rule_args])

    def _rule_with_check_flag(self, rule_args: list[str]) -> list[str]:
        if rule_args[:2] == ["-t", "nat"]:
            return ["iptables", "-t", "nat", "-C", *rule_args[3:]]
        return ["iptables", "-C", *rule_args[1:]]


@dataclass
class TunnelRuntimeState:
    local_tunnel_ready: bool = False
    remote_tunnel_ready: bool = False
    route_override_active: bool = False
    gateway_nat_active: bool = False


# ── Encrypted UDP transport ──────────────────────────────────────────


@dataclass
class UdpTransport:
    """AES-256-GCM encrypted UDP datagram transport with replay protection."""

    send_key: bytes
    recv_key: bytes
    local_port: int
    remote_addr: tuple[str, int]
    _sock: socket.socket | None = field(default=None, init=False, repr=False)
    _send_seq: int = field(default=0, init=False, repr=False)
    _recv_window: int = field(default=0, init=False, repr=False)

    def bind(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("0.0.0.0", self.local_port))
        self._sock.settimeout(0.5)  # non-blocking with short timeout for clean shutdown
        logger.info("UDP transport bound on :%d → %s:%d", self.local_port, *self.remote_addr)

    def close(self) -> None:
        if self._sock:
            self._sock.close()
            self._sock = None

    def send(self, plaintext: bytes) -> None:
        """Encrypt and send a packet."""
        if not self._sock:
            raise RuntimeError("UDP transport not bound")

        self._send_seq += 1
        # 12-byte nonce: 4-byte seq number + 8 zero bytes
        nonce = self._send_seq.to_bytes(SEQ_SIZE, "big") + b"\x00" * 8
        ciphertext = aes_gcm_encrypt(self.send_key, nonce, plaintext)
        frame = self._send_seq.to_bytes(SEQ_SIZE, "big") + ciphertext
        self._sock.sendto(frame, self.remote_addr)

    def recv(self) -> bytes | None:
        """Receive and decrypt a packet. Returns None on timeout or invalid packet."""
        if not self._sock:
            raise RuntimeError("UDP transport not bound")

        try:
            data, _ = self._sock.recvfrom(MAX_PACKET + SEQ_SIZE + 16)
        except (TimeoutError, OSError):
            return None

        if len(data) < SEQ_SIZE + 16:  # seq + minimum GCM tag
            return None

        seq = int.from_bytes(data[:SEQ_SIZE], "big")

        # Basic replay protection: reject packets with seq ≤ last received
        if seq <= self._recv_window:
            logger.warning("Replay detected: seq=%d, window=%d", seq, self._recv_window)
            return None
        self._recv_window = seq

        nonce = seq.to_bytes(SEQ_SIZE, "big") + b"\x00" * 8
        try:
            return aes_gcm_decrypt(self.recv_key, nonce, data[SEQ_SIZE:])
        except Exception:
            logger.warning("Decryption failed for seq=%d", seq)
            return None


# ── Tunnel manager (TUN ↔ UDP forwarding) ────────────────────────────


class TunnelManager:
    """Orchestrates the full tunnel lifecycle: TUN device + encrypted UDP transport.

    Call start() to open the TUN, bind UDP, and begin forwarding in background threads.
    Call stop() to cleanly tear everything down.
    """

    def __init__(
        self,
        tun_name: str,
        tun_address: str,
        tun_prefixlen: int,
        tun_mtu: int,
        udp_send_key: bytes,
        udp_recv_key: bytes,
        udp_local_port: int,
        udp_remote_addr: tuple[str, int],
    ) -> None:
        self.tun = TunDevice(name=tun_name, mtu=tun_mtu)
        self.udp = UdpTransport(
            send_key=udp_send_key,
            recv_key=udp_recv_key,
            local_port=udp_local_port,
            remote_addr=udp_remote_addr,
        )
        self._address = tun_address
        self._prefixlen = tun_prefixlen
        self._running = False
        self._threads: list[threading.Thread] = []
        self._stats = {"packets_sent": 0, "packets_recv": 0, "bytes_sent": 0, "bytes_recv": 0}

    @property
    def stats(self) -> dict[str, int]:
        return dict(self._stats)

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Open TUN, configure interface, bind UDP, start forwarding."""
        _require_linux("Tunnel start")
        if self._running:
            logger.info("TunnelManager.start() ignored; tunnel already running")
            return

        if interface_exists(self.tun.name):
            cleanup_tun_interface(self.tun.name)

        self.tun.open()
        configure_tun(self.tun.name, self._address, self._prefixlen, self.tun.mtu)
        self.udp.bind()

        self._running = True
        t_out = threading.Thread(target=self._forward_tun_to_udp, name="tun→udp", daemon=True)
        t_in = threading.Thread(target=self._forward_udp_to_tun, name="udp→tun", daemon=True)
        self._threads = [t_out, t_in]
        t_out.start()
        t_in.start()
        logger.info("Tunnel started: %s (%s/%d) ↔ UDP :%d", self.tun.name, self._address, self._prefixlen, self.udp.local_port)

    def stop(self) -> None:
        """Stop forwarding, tear down TUN and UDP."""
        if not self._running and not self.tun.is_open and self.udp._sock is None:
            return
        self._running = False

        self.udp.close()
        self.tun.close()

        for t in self._threads:
            t.join(timeout=2.0)
        self._threads.clear()

        try:
            cleanup_tun_interface(self.tun.name)
        except Exception:
            logger.debug("Interface cleanup failed for %s", self.tun.name, exc_info=True)
        logger.info("Tunnel stopped")

    def _forward_tun_to_udp(self) -> None:
        """Read IP packets from TUN → encrypt → send over UDP."""
        while self._running:
            try:
                packet = self.tun.read()
                if packet:
                    self.udp.send(packet)
                    self._stats["packets_sent"] += 1
                    self._stats["bytes_sent"] += len(packet)
            except OSError:
                if self._running:
                    logger.exception("Error reading from TUN")
                break

    def _forward_udp_to_tun(self) -> None:
        """Receive UDP packets → decrypt → write to TUN."""
        while self._running:
            packet = self.udp.recv()
            if packet:
                try:
                    self.tun.write(packet)
                    self._stats["packets_recv"] += 1
                    self._stats["bytes_recv"] += len(packet)
                except OSError:
                    if self._running:
                        logger.exception("Error writing to TUN")
                    break
