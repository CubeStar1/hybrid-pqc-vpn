"""Runtime configuration models."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


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


class AgentConfig(BaseModel):
    runtime_mode: RuntimeMode = RuntimeMode.AGENT
    control_host: str = "127.0.0.1"
    control_port: int = 8765
    api_base_url: str = "http://127.0.0.1:8765"
    linux_vm_target: bool = True
    client_name: str = "rvce-lab-client"
    workspace_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    tun_interface: str = "hyb0"
    tun_address: str = "10.42.0.2"
    tun_prefixlen: int = 24
    udp_local_port: int = 4434
    default_profile: Profile = Field(
        default_factory=lambda: Profile(
            id="lab-gateway",
            name="RVCE Lab Gateway",
            gateway_host="10.0.2.15",
            gateway_port=4433,
        )
    )


class GatewayConfig(BaseModel):
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
