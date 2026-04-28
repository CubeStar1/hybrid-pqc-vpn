from dataclasses import dataclass, field, asdict
from typing import Optional
import msgpack

# --- Message types ---

@dataclass
class HandshakeHello:
    """
    Sent by initiator to responder.
    Contains initiator's public keys and supported algorithm suites.
    """
    session_id: str                   # uuid4 hex string, chosen by initiator
    supported_suites: list[str]       # e.g. ["X25519+MLKEM768+...", "X25519+..."]
    x25519_public_key: bytes          # 32 bytes
    mlkem_public_key: bytes           # ML-KEM-768 public key (~1184 bytes)
    ecdsa_public_key: bytes           # DER-encoded ECDSA-P256 public key
    mldsa_public_key: bytes           # ML-DSA-65 public key
    timestamp: float                  # time.time() — replay protection

@dataclass
class HandshakeResponse:
    """
    Sent by responder to initiator.
    Contains: selected suite, responder's public keys, KEM ciphertext, signatures.
    """
    session_id: str
    selected_suite: str
    x25519_public_key: bytes          # responder's X25519 pub key
    ecdsa_public_key: bytes           # responder's ECDSA pub key
    mldsa_public_key: bytes           # responder's ML-DSA pub key
    mlkem_ciphertext: bytes           # encapsulation of initiator's mlkem_public_key
    # Signature covers: session_id + selected_suite + all pub keys + mlkem_ciphertext
    ecdsa_signature: bytes
    mldsa_signature: bytes
    timestamp: float

@dataclass
class HandshakeFinish:
    """
    Sent by initiator back to responder.
    Proves initiator derived the same session key by MACing a known string.
    """
    session_id: str
    # HMAC-SHA256(mac_key, b"handshake-complete" + session_id.encode())
    mac: bytes
    timestamp: float

# --- Serialization ---

def serialize(msg) -> bytes:
    """Serialize any handshake dataclass to msgpack bytes."""
    return msgpack.packb(asdict(msg), use_bin_type=True)

def deserialize_hello(data: bytes) -> HandshakeHello:
    d = msgpack.unpackb(data, raw=False)
    return HandshakeHello(**d)

def deserialize_response(data: bytes) -> HandshakeResponse:
    d = msgpack.unpackb(data, raw=False)
    return HandshakeResponse(**d)

def deserialize_finish(data: bytes) -> HandshakeFinish:
    d = msgpack.unpackb(data, raw=False)
    return HandshakeFinish(**d)
