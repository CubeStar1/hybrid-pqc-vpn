from __future__ import annotations

from dataclasses import dataclass

try:
    import oqs
except ImportError:  # pragma: no cover - depends on local liboqs install
    oqs = None


ML_KEM_768 = "ML-KEM-768"


@dataclass(slots=True)
class KemArtifacts:
    public_key: bytes
    secret_key: bytes
    ciphertext: bytes
    client_shared_secret: bytes
    server_shared_secret: bytes


def is_oqs_available() -> bool:
    return oqs is not None


def enabled_kem_mechanisms() -> list[str]:
    if oqs is None:  # pragma: no cover - depends on local liboqs install
        return []
    return list(oqs.get_enabled_kem_mechanisms())


def ensure_kem_supported(mechanism: str = ML_KEM_768) -> None:
    if oqs is None:
        raise RuntimeError("liboqs-python is not installed or liboqs is unavailable")
    if mechanism not in enabled_kem_mechanisms():
        raise RuntimeError(f"{mechanism} is not enabled in the current liboqs build")


def perform_kem_roundtrip(mechanism: str = ML_KEM_768) -> KemArtifacts:
    ensure_kem_supported(mechanism)

    with oqs.KeyEncapsulation(mechanism) as server_kem:
        public_key = server_kem.generate_keypair()
        secret_key = server_kem.export_secret_key()
        ciphertext, client_shared_secret = server_kem.encap_secret(public_key)
        server_shared_secret = server_kem.decap_secret(ciphertext)

    return KemArtifacts(
        public_key=public_key,
        secret_key=secret_key,
        ciphertext=ciphertext,
        client_shared_secret=client_shared_secret,
        server_shared_secret=server_shared_secret,
    )
