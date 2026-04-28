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
    ArchitectureCard,
    ClientHelloMessage,
    ConnectRequest,
    ConnectResponse,
    DisconnectResponse,
    PhaseStatus,
    ProjectSnapshot,
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

    # ── Phase tracking ───────────────────────────────────────────────

    def phases(self) -> list[PhaseStatus]:
        return [
            PhaseStatus(
                name="Phase 1",
                status="complete",
                summary="Hybrid cryptographic harness: X25519 + ML-KEM-768, HKDF key schedule, ECDSA-P256 transcript auth.",
            ),
            PhaseStatus(
                name="Phase 2",
                status="complete",
                summary="UDP framing with AES-256-GCM encryption, sequence-number replay protection.",
            ),
            PhaseStatus(
                name="Phase 3",
                status="complete",
                summary="Linux TUN device creation via /dev/net/tun, IP/route management via pyroute2, teardown.",
            ),
            PhaseStatus(
                name="Phase 4",
                status="complete",
                summary="Electron + Next.js desktop dashboard connected to the agent control API.",
            ),
            PhaseStatus(
                name="Phase 5",
                status="planned",
                summary="Metrics, experiments, and report export views come after the first end-to-end control loop.",
            ),
            PhaseStatus(
                name="Phase 6",
                status="planned",
                summary="Hybrid ECDSA + ML-DSA-65 dual-signature authentication.",
            ),
        ]

    # ── Runtime info ─────────────────────────────────────────────────

    def runtime_context(self) -> RuntimeContext:
        return RuntimeContext(
            mode="agent",
            platform=platform.system().lower(),
            linux_vm_target=self.config.linux_vm_target,
            tun_interface=self.config.tun_interface,
            control_api=self.config.resolved_api_base_url,
            notes=[
                "Primary runtime target is a Linux VM for both Electron and the Python tunnel agent.",
                f"TUN interface: {self.config.tun_interface} ({self.config.tun_address}/{self.config.tun_prefixlen})",
                f"UDP data-plane port: {self.config.udp_local_port}",
            ],
        )

    def architecture(self) -> list[ArchitectureCard]:
        return [
            ArchitectureCard(
                title="Desktop Controller",
                description="Electron + Next.js renderer for profile selection, auth, connect/disconnect, logs, and metrics.",
                details=[
                    "Renderer stays unprivileged and talks to the local Python agent over a loopback control API.",
                    "Electron preload exposes runtime context safely instead of granting direct Node access.",
                ],
            ),
            ArchitectureCard(
                title="Hybrid Control Plane",
                description="TLS 1.3-inspired handshake with transcript-bound key derivation.",
                details=[
                    f"Active suite: {SUITE_NAME}.",
                    "Pinned ECDSA-P256 authenticates the transcript.",
                    "ML-KEM-768 via liboqs-python when liboqs is installed.",
                ],
            ),
            ArchitectureCard(
                title="Encrypted Tunnel",
                description="TUN device + AES-256-GCM encrypted UDP transport with replay protection.",
                details=[
                    f"TUN: {self.config.tun_interface} at {self.config.tun_address}/{self.config.tun_prefixlen}",
                    f"UDP local port: {self.config.udp_local_port}, gateway port: {self.config.default_profile.gateway_port}",
                    "Sequence-number nonces prevent replay attacks.",
                ],
            ),
        ]

    def snapshot(self) -> ProjectSnapshot:
        return ProjectSnapshot(
            title="Hybrid Post-Quantum VPN for Linux VMs",
            summary=(
                "A research-grade VPN prototype with a Python control plane, encrypted UDP tunnel, "
                "Linux TUN device management, and an Electron + Next.js desktop controller."
            ),
            architecture=self.architecture(),
            phases=self.phases(),
        )

    # ── Status ───────────────────────────────────────────────────────

    def status(self) -> RuntimeStatus:
        return RuntimeStatus(
            service="hybrid-vpn-agent",
            version="0.1.0",
            runtime=self.runtime_context(),
            phases=self.phases(),
            current_session=self._current_session,
            oqs_available=is_oqs_available(),
            server_identity_ready=True,
        )

    # ── Connect / disconnect ─────────────────────────────────────────

    def connect(self, request: ConnectRequest, gateway_url: str | None = None) -> ConnectResponse:
        """Connect: authenticate → handshake → (optionally) start tunnel."""
        profile = self.config.default_profile
        notes: list[str] = []

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
                notes.append("Gateway authentication succeeded.")
            except httpx.HTTPError:
                notes.append("Gateway unreachable — running local-only handshake.")

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
                notes.append("Hybrid handshake completed with gateway.")
            except Exception as exc:
                notes.append(f"Gateway handshake failed ({exc}), falling back to local demo.")
                self._traffic_secrets = None
        else:
            # Local-only demo handshake
            demo = run_demo_handshake()
            notes.extend(demo.notes)

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
                notes.append(f"Tunnel active: {self.config.tun_interface} ↔ UDP :{self.config.udp_local_port}")
            except Exception as exc:
                notes.append(f"Tunnel creation failed: {exc}")
        elif not IS_LINUX:
            notes.append("Tunnel skipped — requires Linux with root privileges.")

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
            notes=notes,
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
            notes=[f"Disconnected: {reason}"],
        )
        return DisconnectResponse(disconnected=True, message="Session disconnected.")

    def _fail_session(self, request: ConnectRequest, message: str) -> ConnectResponse:
        self._current_session = SessionSummary(
            session_id=str(uuid4()),
            state="error",
            profile_id=request.profile_id,
            username=request.username,
            suite=SUITE_NAME,
            notes=[message],
        )
        return ConnectResponse(accepted=False, message=message, session=self._current_session)
