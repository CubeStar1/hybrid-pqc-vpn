"""Hybrid handshake protocol and key schedule.

Provides both a real client-server handshake (HandshakeClient / HandshakeServer)
and a self-contained demo that runs both sides in-process (run_demo_handshake).
"""

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
from .pqc import (
    ML_KEM_768,
    is_oqs_available,
    kem_decapsulate,
    kem_encapsulate,
    kem_keygen,
    perform_kem_roundtrip,
)


SUITE_NAME = "X25519MLKEM768_AES256GCM_ECDSA_P256"


# ── Shared data structures ──────────────────────────────────────────


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


# ── Key schedule ─────────────────────────────────────────────────────


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


# ── Real client-server handshake protocol ────────────────────────────
#
# Single-round protocol over HTTP:
#   1. Client generates X25519 keypair + ML-KEM keypair (if PQC available).
#   2. Client sends ClientHello {x25519_pub, mlkem_pub?} to gateway.
#   3. Gateway generates X25519 keypair, computes ECDH.
#   4. Gateway encapsulates to client's ML-KEM pub → (ciphertext, pqc_ss).
#   5. Gateway signs transcript with ECDSA, responds with ServerHello.
#   6. Client computes ECDH, decapsulates ML-KEM ciphertext, verifies signature.
#   7. Both sides derive identical TrafficSecrets.


@dataclass(slots=True)
class ClientHelloData:
    """Data the client sends to initiate the handshake."""

    suite: str
    x25519_public: bytes
    mlkem_public: bytes | None  # None if PQC unavailable
    # Kept locally by the client:
    _x25519_private_key: object  # x25519.X25519PrivateKey
    _mlkem_secret_key: bytes | None


@dataclass(slots=True)
class ServerHelloData:
    """Data the server responds with."""

    x25519_public: bytes
    mlkem_ciphertext: bytes | None
    ecdsa_signature: bytes
    ecdsa_public_key_der: bytes
    transcript_hash_hex: str


class HandshakeClient:
    """Client side of the hybrid handshake."""

    def create_hello(self) -> ClientHelloData:
        x25519_priv = generate_x25519_private_key()
        x25519_pub = public_bytes_from_x25519(x25519_priv.public_key())

        mlkem_pub: bytes | None = None
        mlkem_sk: bytes | None = None
        if is_oqs_available():
            kp = kem_keygen(ML_KEM_768)
            mlkem_pub = kp.public_key
            mlkem_sk = kp.secret_key

        return ClientHelloData(
            suite=SUITE_NAME,
            x25519_public=x25519_pub,
            mlkem_public=mlkem_pub,
            _x25519_private_key=x25519_priv,
            _mlkem_secret_key=mlkem_sk,
        )

    def finish(
        self,
        hello: ClientHelloData,
        server_hello: ServerHelloData,
    ) -> TrafficSecrets:
        from cryptography.hazmat.primitives.serialization import load_der_public_key

        # ECDH
        ecdh_ss = derive_x25519_shared_secret(
            hello._x25519_private_key,  # type: ignore[arg-type]
            server_hello.x25519_public,
        )

        # PQC decapsulation
        pqc_ss = b""
        if hello._mlkem_secret_key and server_hello.mlkem_ciphertext:
            pqc_ss = kem_decapsulate(hello._mlkem_secret_key, server_hello.mlkem_ciphertext)

        # Rebuild transcript and verify server signature
        parts = [
            hello.suite.encode(),
            hello.x25519_public,
            server_hello.x25519_public,
        ]
        if hello.mlkem_public:
            parts.append(hello.mlkem_public)
        if server_hello.mlkem_ciphertext:
            parts.append(server_hello.mlkem_ciphertext)

        digest = transcript_hash(parts)
        ecdsa_pub = load_der_public_key(server_hello.ecdsa_public_key_der)
        if not verify_ecdsa(ecdsa_pub, digest, server_hello.ecdsa_signature):  # type: ignore[arg-type]
            raise RuntimeError("Server ECDSA signature verification failed")

        return derive_hybrid_traffic_secrets(ecdh_ss, pqc_ss, digest)


class HandshakeServer:
    """Server side of the hybrid handshake."""

    def __init__(self) -> None:
        # Pinned ECDSA identity key for the server (generated once per service lifetime)
        self._identity_key = generate_ecdsa_private_key()

    @property
    def ecdsa_public_key_der(self) -> bytes:
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

        return self._identity_key.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)

    def process_hello(
        self,
        client_suite: str,
        client_x25519_public: bytes,
        client_mlkem_public: bytes | None,
    ) -> tuple[ServerHelloData, TrafficSecrets]:
        # Server X25519
        server_priv = generate_x25519_private_key()
        server_pub = public_bytes_from_x25519(server_priv.public_key())
        ecdh_ss = derive_x25519_shared_secret(server_priv, client_x25519_public)

        # PQC encapsulation
        pqc_ss = b""
        mlkem_ct: bytes | None = None
        if client_mlkem_public and is_oqs_available():
            enc = kem_encapsulate(client_mlkem_public)
            mlkem_ct = enc.ciphertext
            pqc_ss = enc.shared_secret

        # Transcript
        parts = [client_suite.encode(), client_x25519_public, server_pub]
        if client_mlkem_public:
            parts.append(client_mlkem_public)
        if mlkem_ct:
            parts.append(mlkem_ct)

        digest = transcript_hash(parts)
        signature = sign_ecdsa(self._identity_key, digest)

        traffic = derive_hybrid_traffic_secrets(ecdh_ss, pqc_ss, digest)

        server_hello = ServerHelloData(
            x25519_public=server_pub,
            mlkem_ciphertext=mlkem_ct,
            ecdsa_signature=signature,
            ecdsa_public_key_der=self.ecdsa_public_key_der,
            transcript_hash_hex=digest.hex(),
        )
        return server_hello, traffic


# ── Self-contained demo (CLI and /demo/handshake endpoint) ───────────


def run_demo_handshake() -> HandshakeDemoResult:
    """Run a complete handshake in-process for demonstration purposes."""
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

    transcript_parts = [SUITE_NAME.encode(), client_public_bytes, server_public_bytes]

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
