import oqs

# --- ML-KEM-768 ---

def mlkem_generate_keypair() -> tuple[bytes, bytes]:
    """Returns (private_key_bytes, public_key_bytes)."""
    kem = oqs.KeyEncapsulation("ML-KEM-768")
    public_key = kem.generate_keypair()
    private_key = kem.export_secret_key()
    return private_key, public_key

def mlkem_encapsulate(their_public_key: bytes) -> tuple[bytes, bytes]:
    """
    Run by the responder against the initiator's public key.
    Returns (ciphertext, shared_secret). Send ciphertext to initiator.
    """
    kem = oqs.KeyEncapsulation("ML-KEM-768")
    ciphertext, shared_secret = kem.encap_secret(their_public_key)
    return ciphertext, shared_secret

def mlkem_decapsulate(private_key: bytes, ciphertext: bytes) -> bytes:
    """
    Run by the initiator using their own private key + the ciphertext from responder.
    Returns shared_secret — must match responder's shared_secret byte-for-byte.
    """
    kem = oqs.KeyEncapsulation("ML-KEM-768", secret_key=private_key)
    return kem.decap_secret(ciphertext)


# --- ML-DSA (Dilithium) ---

def mldsa_generate_keypair() -> tuple[bytes, bytes]:
    """Returns (private_key_bytes, public_key_bytes)."""
    signer = oqs.Signature("ML-DSA-65")
    public_key = signer.generate_keypair()
    private_key = signer.export_secret_key()
    return private_key, public_key

def mldsa_sign(private_key: bytes, message: bytes) -> bytes:
    """Returns signature bytes."""
    signer = oqs.Signature("ML-DSA-65", secret_key=private_key)
    return signer.sign(message)

def mldsa_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    """Returns True if valid. Never raises."""
    try:
        verifier = oqs.Signature("ML-DSA-65")
        return verifier.verify(message, signature, public_key)
    except Exception:
        return False
