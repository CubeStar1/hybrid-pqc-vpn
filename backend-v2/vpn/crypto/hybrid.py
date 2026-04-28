from vpn.crypto.kdf import hkdf_derive

def derive_hybrid_session_keys(
    x25519_shared_secret: bytes,
    mlkem_shared_secret: bytes,
    salt: bytes | None = None,
    info: bytes = b"hybrid-vpn-v1"
) -> dict[str, bytes]:
    """
    Concatenates both shared secrets and runs HKDF to derive two 32-byte keys:
      - enc_key: AES-256-GCM encryption key
      - mac_key: reserved for HMAC or other MAC use

    Concatenation order is fixed (x25519 || mlkem) and must be the same on
    both initiator and responder. Changing this order breaks the session.
    
    Returns: {"enc_key": bytes, "mac_key": bytes}
    """
    combined_ikm = x25519_shared_secret + mlkem_shared_secret
    key_material = hkdf_derive(ikm=combined_ikm, length=64, info=info, salt=salt)
    return {
        "enc_key": key_material[:32],
        "mac_key": key_material[32:],
    }

def derive_classical_session_keys(
    x25519_shared_secret: bytes,
    salt: bytes | None = None,
    info: bytes = b"hybrid-vpn-v1"
) -> dict[str, bytes]:
    """
    Classical-only fallback path (no ML-KEM). Used in benchmarking and
    when the peer does not support post-quantum algorithms.
    """
    key_material = hkdf_derive(ikm=x25519_shared_secret, length=64, info=info, salt=salt)
    return {
        "enc_key": key_material[:32],
        "mac_key": key_material[32:],
    }
