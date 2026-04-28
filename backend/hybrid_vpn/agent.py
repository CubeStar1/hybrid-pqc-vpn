"""Agent service — profiles, status, connection lifecycle with real tunnel support."""

from __future__ import annotations

import logging
import platform
from uuid import uuid4

import httpx

from .config import AgentConfig
from .crypto.hybrid import (
    SUITE_NAME,
    HandshakeClient,
    ServerHelloData,
    TrafficSecrets,
)
from .crypto.pqc import is_oqs_available
from .schemas import (
    AgentProfileSummary,
    ClientHelloMessage,
    ConnectRequest,
    ConnectResponse,
    DisconnectResponse,
    RuntimeContext,
    RuntimeStatus,
    SessionSummary,
    ServerHelloMessage,
    TunnelStatus,
)
from .tunnel import ClientRouteManager, IS_LINUX, TunnelManager, TunnelRuntimeState

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self._current_session: SessionSummary | None = None
        self._tunnel: TunnelManager | None = None
        self._traffic_secrets: TrafficSecrets | None = None
        self._route_manager: ClientRouteManager | None = None
        self._runtime_state = TunnelRuntimeState()
        self._active_gateway_url: str | None = None

    # ── Profiles ─────────────────────────────────────────────────────

    def profiles(self) -> list[AgentProfileSummary]:
        profile = self.config.default_profile
        return [
            AgentProfileSummary(
                id=profile.id,
                name=profile.name,
                gateway_host=profile.gateway_host,
                gateway_port=profile.gateway_port,
                tunnel_cidr=profile.tunnel_cidr,
                mtu=profile.mtu,
                supported_suite=profile.supported_suite,
            )
        ]

    # ── Runtime info ─────────────────────────────────────────────────

    def runtime_context(self) -> RuntimeContext:
        return RuntimeContext(
            mode="agent",
            platform=platform.system().lower(),
            linux_vm_target=self.config.linux_vm_target,
            tun_interface=self.config.tun_interface,
            control_api=self.config.resolved_api_base_url,
        )

    # ── Status ───────────────────────────────────────────────────────

    def status(self) -> RuntimeStatus:
        return RuntimeStatus(
            service="hybrid-vpn-agent",
            version="0.1.0",
            runtime=self.runtime_context(),
            current_session=self._current_session,
            oqs_available=is_oqs_available(),
            server_identity_ready=True,
        )

    # ── Connect / disconnect ─────────────────────────────────────────

    def connect(self, request: ConnectRequest, gateway_url: str | None = None) -> ConnectResponse:
        """Connect: authenticate → handshake → gateway session → local tunnel + routing."""
        profile = self.config.default_profile
        gateway_url = gateway_url or self.config.gateway_url

        self._disconnect_internal(gateway_url, "replace-session")
        if not gateway_url:
            return self._fail_session(request, "Gateway URL is required for a real VPN session.")
        if not IS_LINUX:
            return self._fail_session(request, "VPN connect requires Linux with TUN support.")

        # ── Step 1: Authenticate with gateway (if reachable) ─────────
        try:
            auth_resp = httpx.post(
                f"{gateway_url}/auth",
                json={"username": request.username, "password": request.password},
                timeout=5.0,
            )
            if not auth_resp.json().get("authenticated", False):
                return self._fail_session(request, "Gateway authentication failed.")
        except httpx.HTTPError as exc:
            return self._fail_session(request, f"Gateway authentication request failed: {exc}")

        # ── Step 2: Hybrid handshake ─────────────────────────────────
        handshake_client = HandshakeClient()
        client_hello = handshake_client.create_hello()
        server_hello: ServerHelloData | None = None

        try:
            hello_msg = ClientHelloMessage(
                suite=client_hello.suite,
                x25519_public_hex=client_hello.x25519_public.hex(),
                mlkem_public_hex=client_hello.mlkem_public.hex() if client_hello.mlkem_public else None,
            )
            hs_resp = httpx.post(f"{gateway_url}/handshake", json=hello_msg.model_dump(), timeout=5.0)
            server_msg = ServerHelloMessage.model_validate(hs_resp.json())
            server_hello = ServerHelloData(
                x25519_public=bytes.fromhex(server_msg.x25519_public_hex),
                mlkem_ciphertext=bytes.fromhex(server_msg.mlkem_ciphertext_hex) if server_msg.mlkem_ciphertext_hex else None,
                ecdsa_signature=bytes.fromhex(server_msg.ecdsa_signature_hex),
                ecdsa_public_key_der=bytes.fromhex(server_msg.ecdsa_public_key_der_hex),
                transcript_hash_hex=server_msg.transcript_hash_hex,
            )
            self._traffic_secrets = handshake_client.finish(client_hello, server_hello)
        except Exception as exc:
            return self._fail_session(request, f"Gateway handshake failed: {exc}")

        # ── Step 3: Start gateway session, then local tunnel ─────────
        tunnel_status = TunnelStatus()
        try:
            gateway_start = httpx.post(
                f"{gateway_url}/session/start",
                json={
                    "username": request.username,
                    "profile_id": request.profile_id,
                    "client_udp_port": self.config.udp_local_port,
                },
                timeout=5.0,
            )
            gateway_payload = gateway_start.json()
            if not gateway_payload.get("accepted", False):
                return self._fail_session(
                    request,
                    gateway_payload.get("message", "Gateway refused to start the VPN session."),
                )

            self._runtime_state.remote_tunnel_ready = True
            self._runtime_state.gateway_nat_active = bool(
                gateway_payload.get("tunnel", {}).get("gateway_nat_active", False)
            )

            self._tunnel = TunnelManager(
                tun_name=self.config.tun_interface,
                tun_address=self.config.tun_address,
                tun_prefixlen=self.config.tun_prefixlen,
                tun_mtu=profile.mtu,
                udp_send_key=self._traffic_secrets.client_key,
                udp_recv_key=self._traffic_secrets.server_key,
                udp_local_port=self.config.udp_local_port,
                udp_remote_addr=(profile.gateway_host, profile.gateway_port),
            )
            self._tunnel.start()
            self._runtime_state.local_tunnel_ready = True

            self._route_manager = ClientRouteManager(
                tun_name=self.config.tun_interface,
                gateway_host=profile.gateway_host,
            )
            self._route_manager.apply_full_tunnel()
            self._runtime_state.route_override_active = self._route_manager.is_active

            tunnel_status = TunnelStatus(
                active=True,
                tun_device=self.config.tun_interface,
                local_address=f"{self.config.tun_address}/{self.config.tun_prefixlen}",
                remote_endpoint=f"{profile.gateway_host}:{profile.gateway_port}",
                local_tunnel_ready=self._runtime_state.local_tunnel_ready,
                remote_tunnel_ready=self._runtime_state.remote_tunnel_ready,
                route_override_active=self._runtime_state.route_override_active,
                gateway_nat_active=self._runtime_state.gateway_nat_active,
            )
            logger.info("Tunnel active: %s ↔ UDP :%d", self.config.tun_interface, self.config.udp_local_port)
        except Exception as exc:
            logger.error("Tunnel creation failed: %s", exc)
            self._disconnect_internal(gateway_url, "connect-failed")
            return self._fail_session(request, f"Tunnel creation failed: {exc}")

        # ── Step 4: Build session ────────────────────────────────────
        session = SessionSummary(
            session_id=str(uuid4()),
            state="connected",
            profile_id=request.profile_id,
            username=request.username,
            suite=SUITE_NAME,
            transcript_hash_hex=server_hello.transcript_hash_hex if server_hello else None,
            pqc_enabled=is_oqs_available(),
            tunnel=tunnel_status,
        )
        self._current_session = session
        self._active_gateway_url = gateway_url
        return ConnectResponse(accepted=True, message="Session established.", session=session)

    def disconnect(self, reason: str) -> DisconnectResponse:
        if self._current_session is None:
            return DisconnectResponse(disconnected=False, message="No active session.")
        previous = self._current_session
        stats = self._disconnect_internal(self._active_gateway_url or self.config.gateway_url, reason)
        self._current_session = SessionSummary(
            session_id=previous.session_id,
            state="disconnected",
            profile_id=previous.profile_id,
            username=previous.username,
            suite=previous.suite,
            transcript_hash_hex=previous.transcript_hash_hex,
            pqc_enabled=previous.pqc_enabled,
            tunnel=TunnelStatus(active=False, **stats),
        )
        return DisconnectResponse(disconnected=True, message="Session disconnected.")

    def _fail_session(self, request: ConnectRequest, message: str) -> ConnectResponse:
        self._current_session = SessionSummary(
            session_id=str(uuid4()),
            state="error",
            profile_id=request.profile_id,
            username=request.username,
            suite=SUITE_NAME,
        )
        return ConnectResponse(accepted=False, message=message, session=self._current_session)

    def _disconnect_internal(self, gateway_url: str | None, reason: str) -> dict[str, int]:
        stats = self._tunnel.stats if self._tunnel else {
            "packets_sent": 0,
            "packets_recv": 0,
            "bytes_sent": 0,
            "bytes_recv": 0,
        }

        if gateway_url:
            try:
                httpx.post(f"{gateway_url}/session/stop", json={"reason": reason}, timeout=5.0)
            except httpx.HTTPError:
                logger.warning("Gateway stop request failed during %s", reason)

        if self._route_manager and self._route_manager.is_active:
            try:
                self._route_manager.restore()
            finally:
                self._route_manager = None

        if self._tunnel:
            try:
                self._tunnel.stop()
            finally:
                self._tunnel = None

        self._traffic_secrets = None
        self._runtime_state = TunnelRuntimeState()
        self._active_gateway_url = None
        return stats
