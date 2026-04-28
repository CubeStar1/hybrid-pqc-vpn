"""Gateway service — authentication, handshake server, and architecture info."""

from __future__ import annotations

import logging
import platform
from uuid import uuid4

from argon2 import PasswordHasher

from .config import GatewayConfig
from .crypto.hybrid import SUITE_NAME, HandshakeServer, TrafficSecrets
from .crypto.pqc import is_oqs_available
from .schemas import (
    ClientHelloMessage,
    GatewaySessionResponse,
    RuntimeContext,
    RuntimeStatus,
    ServerHelloMessage,
    SessionSummary,
    TunnelStatus,
)
from .tunnel import GatewayNetworkManager, IS_LINUX, TunnelManager, TunnelRuntimeState

logger = logging.getLogger(__name__)


class GatewayService:
    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self._password_hasher = PasswordHasher()
        self._demo_password_hash = self._password_hasher.hash(config.demo_password)
        self._handshake_server = HandshakeServer()
        self._tunnel: TunnelManager | None = None
        self._traffic_secrets: TrafficSecrets | None = None
        self._network: GatewayNetworkManager | None = None
        self._current_session: SessionSummary | None = None
        self._runtime_state = TunnelRuntimeState()
        self._last_transcript_hash_hex: str | None = None

    # ── Authentication ───────────────────────────────────────────────

    def authenticate(self, username: str, password: str) -> bool:
        if username != self.config.demo_username:
            return False
        try:
            return self._password_hasher.verify(self._demo_password_hash, password)
        except Exception:
            return False

    # ── Handshake ────────────────────────────────────────────────────

    def perform_handshake(self, client_hello: ClientHelloMessage) -> ServerHelloMessage:
        """Process a client hello, return server hello. Stores traffic secrets internally."""
        client_x25519_pub = bytes.fromhex(client_hello.x25519_public_hex)
        client_mlkem_pub = (
            bytes.fromhex(client_hello.mlkem_public_hex)
            if client_hello.mlkem_public_hex
            else None
        )

        server_hello_data, traffic = self._handshake_server.process_hello(
            client_suite=client_hello.suite,
            client_x25519_public=client_x25519_pub,
            client_mlkem_public=client_mlkem_pub,
        )
        self._traffic_secrets = traffic
        self._last_transcript_hash_hex = server_hello_data.transcript_hash_hex

        return ServerHelloMessage(
            x25519_public_hex=server_hello_data.x25519_public.hex(),
            mlkem_ciphertext_hex=(
                server_hello_data.mlkem_ciphertext.hex()
                if server_hello_data.mlkem_ciphertext
                else None
            ),
            ecdsa_signature_hex=server_hello_data.ecdsa_signature.hex(),
            ecdsa_public_key_der_hex=server_hello_data.ecdsa_public_key_der.hex(),
            transcript_hash_hex=server_hello_data.transcript_hash_hex,
        )

    # ── Runtime info ─────────────────────────────────────────────────

    def runtime_context(self) -> RuntimeContext:
        return RuntimeContext(
            mode="gateway",
            platform=platform.system().lower(),
            linux_vm_target=True,
            tun_interface=self.config.tun_interface,
        )

    def status(self) -> RuntimeStatus:
        return RuntimeStatus(
            service="hybrid-vpn-gateway",
            version="0.1.0",
            runtime=self.runtime_context(),
            current_session=self._current_session,
            oqs_available=is_oqs_available(),
            server_identity_ready=True,
        )

    # ── Tunnel lifecycle ─────────────────────────────────────────────

    def start_tunnel(self, client_addr: tuple[str, int]) -> TunnelStatus:
        """Start the gateway-side TUN + UDP tunnel after a successful handshake."""
        if not self._traffic_secrets:
            raise RuntimeError("Cannot start tunnel without completing handshake first")
        if not IS_LINUX:
            raise RuntimeError("Gateway tunnel requires Linux with TUN support")

        self._tunnel = TunnelManager(
            tun_name=self.config.tun_interface,
            tun_address=self.config.tun_address,
            tun_prefixlen=self.config.tun_prefixlen,
            tun_mtu=1280,
            udp_send_key=self._traffic_secrets.server_key,
            udp_recv_key=self._traffic_secrets.client_key,
            udp_local_port=self.config.udp_port,
            udp_remote_addr=client_addr,
        )
        self._tunnel.start()
        self._runtime_state.local_tunnel_ready = True
        self._runtime_state.remote_tunnel_ready = True

        if self.config.full_tunnel_enabled:
            if not self.config.uplink_iface:
                raise RuntimeError("Gateway uplink interface is required for full-tunnel mode")
            self._network = GatewayNetworkManager(
                tun_name=self.config.tun_interface,
                tunnel_cidr=self.config.tunnel_pool,
                uplink_iface=self.config.uplink_iface,
            )
            self._network.apply()
            self._runtime_state.gateway_nat_active = self._network.is_active

        logger.info("Gateway tunnel started")
        return TunnelStatus(
            active=True,
            tun_device=self.config.tun_interface,
            local_address=f"{self.config.tun_address}/{self.config.tun_prefixlen}",
            remote_endpoint=f"{client_addr[0]}:{client_addr[1]}",
            local_tunnel_ready=self._runtime_state.local_tunnel_ready,
            remote_tunnel_ready=self._runtime_state.remote_tunnel_ready,
            route_override_active=False,
            gateway_nat_active=self._runtime_state.gateway_nat_active,
        )

    def stop_tunnel(self) -> None:
        if self._tunnel:
            self._tunnel.stop()
        self._tunnel = None
        logger.info("Gateway tunnel stopped")

    def start_session(self, username: str, profile_id: str, client_addr: tuple[str, int]) -> GatewaySessionResponse:
        if not self._traffic_secrets:
            raise RuntimeError("Handshake must complete before starting a gateway session")

        traffic = self._traffic_secrets
        transcript_hash_hex = self._last_transcript_hash_hex
        self.stop_session("replace-session")
        self._traffic_secrets = traffic
        self._last_transcript_hash_hex = transcript_hash_hex
        tunnel = None
        try:
            tunnel = self.start_tunnel(client_addr)
            session_id = str(uuid4())
            self._current_session = SessionSummary(
                session_id=session_id,
                state="connected",
                profile_id=profile_id,
                username=username,
                suite=SUITE_NAME,
                transcript_hash_hex=self._last_transcript_hash_hex,
                pqc_enabled=is_oqs_available(),
                tunnel=tunnel,
            )
            return GatewaySessionResponse(
                accepted=True,
                message="Gateway session established.",
                tunnel=tunnel,
                session_id=session_id,
            )
        except Exception:
            self.stop_session("start-failed")
            raise

    def stop_session(self, reason: str) -> GatewaySessionResponse:
        del reason
        if self._network and self._network.is_active:
            try:
                self._network.teardown()
            finally:
                self._network = None
        self.stop_tunnel()
        self._traffic_secrets = None
        self._last_transcript_hash_hex = None
        self._runtime_state = TunnelRuntimeState()
        self._current_session = None
        return GatewaySessionResponse(accepted=True, message="Gateway session stopped.")

    @property
    def tunnel_stats(self) -> dict[str, int]:
        if self._tunnel:
            return self._tunnel.stats
        return {"packets_sent": 0, "packets_recv": 0, "bytes_sent": 0, "bytes_recv": 0}
