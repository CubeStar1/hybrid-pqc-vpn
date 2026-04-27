from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

from .classical import (
    derive_x25519_shared_secret,
    generate_ecdsa_private_key,
    generate_x25519_private_key,
    hkdf_expand,
    public_bytes_from_x25519,
    sign_ecdsa,
    transcript_hash,
    verify_ecdsa,
)
from .pqc import ML_KEM_768, is_oqs_available, perform_kem_roundtrip


SUITE_NAME = "X25519MLKEM768_AES256GCM_ECDSA_P256"


@dataclass(slots=True)
class TrafficSecrets:
    client_key: bytes
    server_key: bytes
    client_nonce_base: bytes
    server_nonce_base: bytes


class HandshakeDemoResult(BaseModel):
    suite: str = SUITE_NAME
    oqs_available: bool
    authentication_verified: bool
    transcript_hash_hex: str
    transcript_bytes: int
    client_key_hex: str | None = None
    server_key_hex: str | None = None
    client_nonce_base_hex: str | None = None
    server_nonce_base_hex: str | None = None
    ecdh_public_bytes: int
    mlkem_public_bytes: int | None = None
    mlkem_ciphertext_bytes: int | None = None
    notes: list[str] = Field(default_factory=list)


def derive_hybrid_traffic_secrets(
    ecdh_shared_secret: bytes,
    pqc_shared_secret: bytes,
    transcript_digest: bytes,
) -> TrafficSecrets:
    combined_secret = pqc_shared_secret + ecdh_shared_secret
    return TrafficSecrets(
        client_key=hkdf_expand(b"rvce client traffic", combined_secret, transcript_digest, 32),
        server_key=hkdf_expand(b"rvce server traffic", combined_secret, transcript_digest, 32),
        client_nonce_base=hkdf_expand(b"rvce client nonce", combined_secret, transcript_digest, 12),
        server_nonce_base=hkdf_expand(b"rvce server nonce", combined_secret, transcript_digest, 12),
    )


def run_demo_handshake() -> HandshakeDemoResult:
    client_private = generate_x25519_private_key()
    server_private = generate_x25519_private_key()
    client_public_bytes = public_bytes_from_x25519(client_private.public_key())
    server_public_bytes = public_bytes_from_x25519(server_private.public_key())
    client_ecdh = derive_x25519_shared_secret(client_private, server_public_bytes)
    server_ecdh = derive_x25519_shared_secret(server_private, client_public_bytes)
    notes = ["ECDSA-P256 transcript authentication is active for the MVP harness."]

    pqc_public_size: int | None = None
    pqc_ciphertext_size: int | None = None
    client_key_hex: str | None = None
    server_key_hex: str | None = None
    client_nonce_base_hex: str | None = None
    server_nonce_base_hex: str | None = None
    oqs_available = is_oqs_available()

    transcript_parts = [
        SUITE_NAME.encode(),
        client_public_bytes,
        server_public_bytes,
    ]

    if oqs_available:
        kem_roundtrip = perform_kem_roundtrip(ML_KEM_768)
        if kem_roundtrip.client_shared_secret != kem_roundtrip.server_shared_secret:
            raise RuntimeError("ML-KEM roundtrip produced mismatched shared secrets")

        transcript_parts.extend([kem_roundtrip.public_key, kem_roundtrip.ciphertext])
        pqc_public_size = len(kem_roundtrip.public_key)
        pqc_ciphertext_size = len(kem_roundtrip.ciphertext)
        traffic = derive_hybrid_traffic_secrets(
            ecdh_shared_secret=client_ecdh,
            pqc_shared_secret=kem_roundtrip.client_shared_secret,
            transcript_digest=transcript_hash(transcript_parts),
        )
        client_key_hex = traffic.client_key.hex()
        server_key_hex = traffic.server_key.hex()
        client_nonce_base_hex = traffic.client_nonce_base.hex()
        server_nonce_base_hex = traffic.server_nonce_base.hex()
        notes.append("ML-KEM-768 shared secret is concatenated before X25519 in the key schedule.")
    else:
        notes.append("liboqs is unavailable, so the API is running without a live ML-KEM harness.")

    if client_ecdh != server_ecdh:
        raise RuntimeError("X25519 key exchange produced mismatched secrets")

    digest = transcript_hash(transcript_parts)
    server_identity = generate_ecdsa_private_key()
    signature = sign_ecdsa(server_identity, digest)
    auth_verified = verify_ecdsa(server_identity.public_key(), digest, signature)

    return HandshakeDemoResult(
        oqs_available=oqs_available,
        authentication_verified=auth_verified,
        transcript_hash_hex=digest.hex(),
        transcript_bytes=sum(len(part) for part in transcript_parts),
        client_key_hex=client_key_hex,
        server_key_hex=server_key_hex,
        client_nonce_base_hex=client_nonce_base_hex,
        server_nonce_base_hex=server_nonce_base_hex,
        ecdh_public_bytes=len(client_public_bytes),
        mlkem_public_bytes=pqc_public_size,
        mlkem_ciphertext_bytes=pqc_ciphertext_size,
        notes=notes,
    )
