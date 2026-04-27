from __future__ import annotations

from argon2 import PasswordHasher

from .config import GatewayConfig
from .schemas import ArchitectureCard


class GatewayService:
    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self._password_hasher = PasswordHasher()
        self._demo_password_hash = self._password_hasher.hash(config.demo_password)

    def authenticate(self, username: str, password: str) -> bool:
        if username != self.config.demo_username:
            return False
        try:
            return self._password_hasher.verify(self._demo_password_hash, password)
        except Exception:
            return False

    def architecture_cards(self) -> list[ArchitectureCard]:
        return [
            ArchitectureCard(
                title="Gateway Control Plane",
                description="Owns auth, session policy, and tunnel lifecycle.",
                details=[
                    "Pinned ECDSA-P256 server identity for MVP authentication.",
                    "ML-DSA-65 is planned after the tunnel and client control flow are stable.",
                    "Exposes a clear split between control-plane auth and future UDP data-plane handling.",
                ],
            ),
            ArchitectureCard(
                title="Linux VM Runtime",
                description="Targets a clean Linux network stack instead of host-specific workarounds.",
                details=[
                    "Systemd-ready deployment path for demos inside VMware, VirtualBox, or Hyper-V guests.",
                    "TUN and route orchestration remain intentionally isolated to Linux.",
                ],
            ),
        ]
