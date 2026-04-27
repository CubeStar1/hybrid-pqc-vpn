"""Post-quantum KEM helpers (ML-KEM-768 via liboqs)."""

from __future__ import annotations

from dataclasses import dataclass

try:
    import oqs
except ImportError:  # pragma: no cover - depends on local liboqs install
    oqs = None


ML_KEM_768 = "ML-KEM-768"


@dataclass(slots=True)
class KemKeypair:
    public_key: bytes
    secret_key: bytes


@dataclass(slots=True)
class KemEncapsulation:
    ciphertext: bytes
    shared_secret: bytes


@dataclass(slots=True)
class KemArtifacts:
    """Full roundtrip result (used by the CLI demo command)."""

    public_key: bytes
    secret_key: bytes
    ciphertext: bytes
    client_shared_secret: bytes
    server_shared_secret: bytes


def is_oqs_available() -> bool:
    return oqs is not None


def enabled_kem_mechanisms() -> list[str]:
    if oqs is None:  # pragma: no cover
        return []
    return list(oqs.get_enabled_kem_mechanisms())


def ensure_kem_supported(mechanism: str = ML_KEM_768) -> None:
    if oqs is None:
        raise RuntimeError("liboqs-python is not installed or liboqs is unavailable")
    if mechanism not in enabled_kem_mechanisms():
        raise RuntimeError(f"{mechanism} is not enabled in the current liboqs build")


# ── Split operations for real client-server handshake ────────────────


def kem_keygen(mechanism: str = ML_KEM_768) -> KemKeypair:
    """Generate an ML-KEM keypair. Returns (public_key, secret_key)."""
    ensure_kem_supported(mechanism)
    with oqs.KeyEncapsulation(mechanism) as kem:
        public_key = kem.generate_keypair()
        secret_key = kem.export_secret_key()
    return KemKeypair(public_key=public_key, secret_key=secret_key)


def kem_encapsulate(public_key: bytes, mechanism: str = ML_KEM_768) -> KemEncapsulation:
    """Encapsulate to a public key. Returns (ciphertext, shared_secret)."""
    ensure_kem_supported(mechanism)
    with oqs.KeyEncapsulation(mechanism) as kem:
        ciphertext, shared_secret = kem.encap_secret(public_key)
    return KemEncapsulation(ciphertext=ciphertext, shared_secret=shared_secret)


def kem_decapsulate(
    secret_key: bytes,
    ciphertext: bytes,
    mechanism: str = ML_KEM_768,
) -> bytes:
    """Decapsulate with a secret key. Returns shared_secret."""
    ensure_kem_supported(mechanism)
    with oqs.KeyEncapsulation(mechanism, secret_key=secret_key) as kem:
        return kem.decap_secret(ciphertext)


# ── All-in-one roundtrip (CLI demo) ─────────────────────────────────


def perform_kem_roundtrip(mechanism: str = ML_KEM_768) -> KemArtifacts:
    """Run a complete KEM roundtrip in-process (for the demo-handshake CLI)."""
    kp = kem_keygen(mechanism)
    enc = kem_encapsulate(kp.public_key, mechanism)
    server_ss = kem_decapsulate(kp.secret_key, enc.ciphertext, mechanism)
    return KemArtifacts(
        public_key=kp.public_key,
        secret_key=kp.secret_key,
        ciphertext=enc.ciphertext,
        client_shared_secret=enc.shared_secret,
        server_shared_secret=server_ss,
    )
