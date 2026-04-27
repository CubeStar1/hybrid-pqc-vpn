"""Runtime configuration models with environment-variable overrides."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeMode(str, Enum):
    AGENT = "agent"
    GATEWAY = "gateway"


class Profile(BaseModel):
    id: str
    name: str
    gateway_host: str
    gateway_port: int = 4433
    tunnel_cidr: str = "10.42.0.0/24"
    mtu: int = 1280
    supported_suite: str = "X25519MLKEM768_AES256GCM_ECDSA_P256"


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HYBRID_VPN_AGENT_",
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    runtime_mode: RuntimeMode = RuntimeMode.AGENT
    control_host: str = "127.0.0.1"
    control_port: int = 8765
    api_base_url: str | None = None
    gateway_url: str | None = None
    linux_vm_target: bool = True
    client_name: str = "rvce-lab-client"
    workspace_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    tun_interface: str = "hyb0"
    tun_address: str = "10.42.0.2"
    tun_prefixlen: int = 24
    udp_local_port: int = 4434
    profile_id: str = "lab-gateway"
    profile_name: str = "RVCE Lab Gateway"
    gateway_host: str = "10.0.2.15"
    gateway_port: int = 4433
    tunnel_cidr: str = "10.42.0.0/24"
    mtu: int = 1280
    supported_suite: str = "X25519MLKEM768_AES256GCM_ECDSA_P256"

    @computed_field(return_type=Profile)
    @property
    def default_profile(self) -> Profile:
        return Profile(
            id=self.profile_id,
            name=self.profile_name,
            gateway_host=self.gateway_host,
            gateway_port=self.gateway_port,
            tunnel_cidr=self.tunnel_cidr,
            mtu=self.mtu,
            supported_suite=self.supported_suite,
        )

    @computed_field(return_type=str)
    @property
    def resolved_api_base_url(self) -> str:
        return self.api_base_url or f"http://{self.control_host}:{self.control_port}"


class GatewayConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HYBRID_VPN_GATEWAY_",
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    runtime_mode: RuntimeMode = RuntimeMode.GATEWAY
    listen_host: str = "0.0.0.0"
    listen_port: int = 9876
    udp_port: int = 4433
    server_name: str = "rvce-hybrid-gateway"
    tun_interface: str = "hyb-gw0"
    tun_address: str = "10.42.0.1"
    tun_prefixlen: int = 24
    tunnel_pool: str = "10.42.0.0/24"
    pinned_server_key_id: str = "server-ecdsa-p256-dev"
    demo_username: str = "demo"
    demo_password: str = "demo-vpn-2026"
