from dataclasses import dataclass, field
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class VPNConfig:
    # Network
    server_host: str = "0.0.0.0"
    server_port: int = 51820
    api_port: int = 8000
    tun_name: str = "vpn0"
    tun_mtu: int = 1420

    # Cryptography
    supported_algo_suites: List[str] = field(default_factory=lambda: [
        "X25519+MLKEM768+AESGCM+ECDSA+MLDSA",   # hybrid (preferred)
        "X25519+AESGCM+ECDSA",                    # classical fallback
    ])
    aes_key_len: int = 32          # bytes — AES-256
    nonce_len: int = 12            # bytes — 96-bit nonce for GCM
    hkdf_info: bytes = b"hybrid-vpn-v1"

    # Session
    session_timeout_seconds: int = 3600
    rekey_after_packets: int = 100_000
    rekey_after_seconds: int = 900

    # TLS / API
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000"])

def load_config() -> VPNConfig:
    cfg = VPNConfig()
    cfg.server_host = os.getenv("VPN_HOST", cfg.server_host)
    cfg.server_port = int(os.getenv("VPN_PORT", cfg.server_port))
    cfg.api_port = int(os.getenv("API_PORT", cfg.api_port))
    return cfg

config = load_config()
