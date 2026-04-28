import pytest
from vpn.crypto.classical import (
    x25519_generate_keypair, x25519_compute_shared_secret,
    ecdsa_generate_keypair, ecdsa_sign, ecdsa_verify,
    aes_gcm_encrypt, aes_gcm_decrypt
)

def test_x25519_shared_secret_symmetric():
    """Both sides must derive the same DH secret."""
    priv_a, pub_a = x25519_generate_keypair()
    priv_b, pub_b = x25519_generate_keypair()
    assert x25519_compute_shared_secret(priv_a, pub_b) == x25519_compute_shared_secret(priv_b, pub_a)

def test_x25519_different_keypairs_different_secrets():
    priv_a, pub_a = x25519_generate_keypair()
    priv_b, pub_b = x25519_generate_keypair()
    priv_c, pub_c = x25519_generate_keypair()
    assert x25519_compute_shared_secret(priv_a, pub_b) != x25519_compute_shared_secret(priv_a, pub_c)

def test_ecdsa_sign_verify_roundtrip():
    priv, pub = ecdsa_generate_keypair()
    message = b"test message for signing"
    sig = ecdsa_sign(priv, message)
    assert ecdsa_verify(pub, message, sig) is True

def test_ecdsa_rejects_tampered_message():
    priv, pub = ecdsa_generate_keypair()
    sig = ecdsa_sign(priv, b"original")
    assert ecdsa_verify(pub, b"tampered", sig) is False

def test_aes_gcm_roundtrip():
    import os
    key = os.urandom(32)
    plaintext = b"secret tunnel data"
    aad = b"packet-header"
    nonce, ct = aes_gcm_encrypt(key, plaintext, aad)
    recovered = aes_gcm_decrypt(key, nonce, ct, aad)
    assert recovered == plaintext

def test_aes_gcm_rejects_tampered_ciphertext():
    from cryptography.exceptions import InvalidTag
    import os
    key = os.urandom(32)
    nonce, ct = aes_gcm_encrypt(key, b"data", b"aad")
    tampered = ct[:-1] + bytes([ct[-1] ^ 0xFF])
    with pytest.raises(InvalidTag):
        aes_gcm_decrypt(key, nonce, tampered, b"aad")
