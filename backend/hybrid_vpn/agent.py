from __future__ import annotations

import platform
from uuid import uuid4

from .config import AgentConfig
from .crypto.hybrid import SUITE_NAME, run_demo_handshake
from .crypto.pqc import is_oqs_available
from .gateway import GatewayService
from .schemas import (
    AgentProfileSummary,
    ArchitectureCard,
    ConnectRequest,
    ConnectResponse,
    DisconnectResponse,
    PhaseStatus,
    ProjectSnapshot,
    RuntimeContext,
    RuntimeStatus,
    SessionSummary,
)
from .system import build_tun_provision_plan


class AgentService:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self._current_session: SessionSummary | None = None

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

    def phases(self) -> list[PhaseStatus]:
        return [
            PhaseStatus(
                name="Phase 1",
                status="complete",
                summary="Hybrid cryptographic harness for X25519, HKDF, and optional ML-KEM-768 is scaffolded.",
            ),
            PhaseStatus(
                name="Phase 2",
                status="in_progress",
                summary="UDP tunnel framing and encrypted packet transport are represented in the architecture but not wired live yet.",
            ),
            PhaseStatus(
                name="Phase 3",
                status="planned",
                summary="Linux TUN interface bring-up, routing, and teardown are defined but intentionally non-mutating.",
            ),
            PhaseStatus(
                name="Phase 4",
                status="in_progress",
                summary="Electron-to-agent control flow and status surfaces are now scaffolded for the desktop app.",
            ),
            PhaseStatus(
                name="Phase 5",
                status="planned",
                summary="Metrics, experiments, and report export views come after the first end-to-end control loop.",
            ),
            PhaseStatus(
                name="Phase 6",
                status="planned",
                summary="Hybrid ECDSA plus ML-DSA authentication is scheduled after the tunnel path is stable.",
            ),
        ]

    def runtime_context(self) -> RuntimeContext:
        return RuntimeContext(
            mode="agent",
            platform=platform.system().lower(),
            linux_vm_target=self.config.linux_vm_target,
            tun_interface=self.config.tun_interface,
            control_api=self.config.api_base_url,
            notes=[
                "Primary runtime target is a Linux VM for both Electron and the Python tunnel agent.",
                "The current scaffold avoids mutating routes or interfaces until the data-plane milestone lands.",
            ],
        )

    def architecture(self) -> list[ArchitectureCard]:
        tun_plan = build_tun_provision_plan(
            interface_name=self.config.tun_interface,
            mtu=self.config.default_profile.mtu,
            cidr=self.config.default_profile.tunnel_cidr,
        )
        return [
            ArchitectureCard(
                title="Desktop Controller",
                description="Electron + Next.js renderer for profile selection, auth, connect/disconnect, logs, and metrics.",
                details=[
                    "Renderer stays unprivileged and talks to the local Python agent over a loopback control API.",
                    "Electron preload exposes runtime context safely instead of granting direct Node access in the page.",
                ],
            ),
            ArchitectureCard(
                title="Hybrid Control Plane",
                description="TLS 1.3-inspired handshake with transcript-bound key derivation.",
                details=[
                    f"Single active suite: {SUITE_NAME}.",
                    "Pinned ECDSA-P256 authenticates the transcript in MVP.",
                    "ML-KEM-768 is expected through liboqs-python when the runtime has liboqs installed.",
                ],
            ),
            ArchitectureCard(
                title="Linux Tunnel Plan",
                description="TUN, routes, and VM networking remain Linux-native from the beginning.",
                details=tun_plan.notes,
            ),
        ]

    def snapshot(self) -> ProjectSnapshot:
        return ProjectSnapshot(
            title="Hybrid Post-Quantum VPN for Linux VMs",
            summary=(
                "A research-grade VPN prototype with a Python control plane, a Linux-native tunnel engine, "
                "and a desktop controller built in Electron + Next.js."
            ),
            architecture=self.architecture(),
            phases=self.phases(),
        )

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

    def connect(self, request: ConnectRequest, gateway: GatewayService | None = None) -> ConnectResponse:
        if gateway is not None and not gateway.authenticate(request.username, request.password):
            self._current_session = SessionSummary(
                session_id=str(uuid4()),
                state="error",
                profile_id=request.profile_id,
                username=request.username,
                suite=SUITE_NAME,
                notes=["Gateway authentication failed for the provided username/password pair."],
            )
            return ConnectResponse(
                accepted=False,
                message="Authentication failed. Use the configured demo gateway credentials.",
                session=self._current_session,
            )

        demo = run_demo_handshake()
        session = SessionSummary(
            session_id=str(uuid4()),
            state="connected" if demo.authentication_verified else "error",
            profile_id=request.profile_id,
            username=request.username,
            suite=demo.suite,
            transcript_hash_hex=demo.transcript_hash_hex,
            pqc_enabled=demo.oqs_available,
            notes=[
                "This session represents the implemented control-plane harness and desktop integration path.",
                "UDP transport, TUN attach, and live routing are the next execution milestones.",
                *demo.notes,
            ],
        )
        self._current_session = session
        return ConnectResponse(
            accepted=demo.authentication_verified,
            message="Hybrid control-plane demo session created.",
            session=session,
        )

    def disconnect(self, reason: str) -> DisconnectResponse:
        if self._current_session is None:
            return DisconnectResponse(disconnected=False, message="No active session is present.")
        self._current_session = SessionSummary(
            session_id=self._current_session.session_id,
            state="disconnected",
            profile_id=self._current_session.profile_id,
            username=self._current_session.username,
            suite=self._current_session.suite,
            transcript_hash_hex=self._current_session.transcript_hash_hex,
            pqc_enabled=self._current_session.pqc_enabled,
            notes=[f"Disconnected from the local agent: {reason}"],
        )
        return DisconnectResponse(disconnected=True, message="Session disconnected.")
