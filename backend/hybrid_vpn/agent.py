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
    run_demo_handshake,
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
from .tunnel import IS_LINUX, TunnelManager

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self._current_session: SessionSummary | None = None
        self._tunnel: TunnelManager | None = None
        self._traffic_secrets: TrafficSecrets | None = None

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
        """Connect: authenticate → handshake → (optionally) start tunnel."""
        profile = self.config.default_profile

        # ── Step 1: Authenticate with gateway (if reachable) ─────────
        if gateway_url:
            try:
                auth_resp = httpx.post(
                    f"{gateway_url}/auth",
                    json={"username": request.username, "password": request.password},
                    timeout=5.0,
                )
                if not auth_resp.json().get("authenticated", False):
                    return self._fail_session(request, "Gateway authentication failed.")
            except httpx.HTTPError:
                logger.warning("Gateway unreachable — running local-only handshake.")

        # ── Step 2: Hybrid handshake ─────────────────────────────────
        handshake_client = HandshakeClient()
        client_hello = handshake_client.create_hello()

        if gateway_url:
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
                traffic_secrets = handshake_client.finish(client_hello, server_hello)
                self._traffic_secrets = traffic_secrets
            except Exception as exc:
                logger.warning("Gateway handshake failed (%s), falling back to local demo.", exc)
                self._traffic_secrets = None
        else:
            # Local-only demo handshake
            run_demo_handshake()

        # ── Step 3: Start tunnel (Linux only) ────────────────────────
        tunnel_status = TunnelStatus()
        if IS_LINUX and self._traffic_secrets:
            try:
                self._tunnel = TunnelManager(
                    tun_name=self.config.tun_interface,
                    tun_address=self.config.tun_address,
                    tun_prefixlen=self.config.tun_prefixlen,
                    tun_mtu=profile.mtu,
                    udp_key=self._traffic_secrets.client_key,
                    udp_local_port=self.config.udp_local_port,
                    udp_remote_addr=(profile.gateway_host, profile.gateway_port),
                )
                self._tunnel.start()
                tunnel_status = TunnelStatus(
                    active=True,
                    tun_device=self.config.tun_interface,
                    local_address=f"{self.config.tun_address}/{self.config.tun_prefixlen}",
                    remote_endpoint=f"{profile.gateway_host}:{profile.gateway_port}",
                )
                logger.info("Tunnel active: %s ↔ UDP :%d", self.config.tun_interface, self.config.udp_local_port)
            except Exception as exc:
                logger.error("Tunnel creation failed: %s", exc)
        elif not IS_LINUX:
            logger.info("Tunnel skipped — requires Linux with root privileges.")

        # ── Step 4: Build session ────────────────────────────────────
        session = SessionSummary(
            session_id=str(uuid4()),
            state="connected",
            profile_id=request.profile_id,
            username=request.username,
            suite=SUITE_NAME,
            transcript_hash_hex=server_hello.transcript_hash_hex if gateway_url and self._traffic_secrets else None,
            pqc_enabled=is_oqs_available(),
            tunnel=tunnel_status,
        )
        self._current_session = session
        return ConnectResponse(accepted=True, message="Session established.", session=session)

    def disconnect(self, reason: str) -> DisconnectResponse:
        if self._current_session is None:
            return DisconnectResponse(disconnected=False, message="No active session.")

        # Stop tunnel if running
        if self._tunnel and self._tunnel.is_running:
            stats = self._tunnel.stats
            self._tunnel.stop()
            self._tunnel = None
        else:
            stats = {"packets_sent": 0, "packets_recv": 0, "bytes_sent": 0, "bytes_recv": 0}

        self._current_session = SessionSummary(
            session_id=self._current_session.session_id,
            state="disconnected",
            profile_id=self._current_session.profile_id,
            username=self._current_session.username,
            suite=self._current_session.suite,
            transcript_hash_hex=self._current_session.transcript_hash_hex,
            pqc_enabled=self._current_session.pqc_enabled,
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
