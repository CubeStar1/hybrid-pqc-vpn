"""Gateway service — authentication, handshake server, and architecture info."""

from __future__ import annotations

import logging

from argon2 import PasswordHasher

from .config import GatewayConfig
from .crypto.hybrid import HandshakeServer, TrafficSecrets
from .schemas import ClientHelloMessage, ServerHelloMessage
from .tunnel import IS_LINUX, TunnelManager

logger = logging.getLogger(__name__)


class GatewayService:
    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self._password_hasher = PasswordHasher()
        self._demo_password_hash = self._password_hasher.hash(config.demo_password)
        self._handshake_server = HandshakeServer()
        self._tunnel: TunnelManager | None = None
        self._traffic_secrets: TrafficSecrets | None = None

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

    # ── Tunnel lifecycle ─────────────────────────────────────────────

    def start_tunnel(self, client_addr: tuple[str, int]) -> None:
        """Start the gateway-side TUN + UDP tunnel after a successful handshake."""
        if not self._traffic_secrets:
            raise RuntimeError("Cannot start tunnel without completing handshake first")
        if not IS_LINUX:
            logger.warning("Tunnel start skipped — not running on Linux")
            return

        self._tunnel = TunnelManager(
            tun_name=self.config.tun_interface,
            tun_address=self.config.tun_address,
            tun_prefixlen=self.config.tun_prefixlen,
            tun_mtu=1280,
            udp_key=self._traffic_secrets.server_key,
            udp_local_port=self.config.udp_port,
            udp_remote_addr=client_addr,
        )
        self._tunnel.start()
        logger.info("Gateway tunnel started")

    def stop_tunnel(self) -> None:
        if self._tunnel and self._tunnel.is_running:
            self._tunnel.stop()
            self._tunnel = None
            logger.info("Gateway tunnel stopped")

    @property
    def tunnel_stats(self) -> dict[str, int]:
        if self._tunnel:
            return self._tunnel.stats
        return {"packets_sent": 0, "packets_recv": 0, "bytes_sent": 0, "bytes_recv": 0}

