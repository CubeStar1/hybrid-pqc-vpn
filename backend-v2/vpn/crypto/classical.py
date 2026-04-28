from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, PrivateFormat, NoEncryption
)
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def x25519_generate_keypair() -> tuple[bytes, bytes]:
    """Returns (private_key_bytes, public_key_bytes). Both are 32-byte raw."""
    private_key = X25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    public_bytes = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return private_bytes, public_bytes

def x25519_compute_shared_secret(my_private_bytes: bytes, their_public_bytes: bytes) -> bytes:
    """Returns 32-byte raw shared secret. Raises ValueError on invalid inputs."""
    private_key = X25519PrivateKey.from_private_bytes(my_private_bytes)
    public_key = X25519PublicKey.from_public_bytes(their_public_bytes)
    return private_key.exchange(public_key)

def ecdsa_generate_keypair() -> tuple[bytes, bytes]:
    """Returns (private_key_der_bytes, public_key_der_bytes)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_der = private_key.private_bytes(
        Encoding.DER, PrivateFormat.PKCS8, NoEncryption()
    )
    public_der = private_key.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)
    return private_der, public_der

def ecdsa_sign(private_key_der: bytes, message: bytes) -> bytes:
    """Returns DER-encoded signature bytes."""
    private_key = serialization.load_der_private_key(private_key_der, password=None)
    return private_key.sign(message, ec.ECDSA(hashes.SHA256()))

def ecdsa_verify(public_key_der: bytes, message: bytes, signature: bytes) -> bool:
    """Returns True if valid, False if not. Never raises on bad sig."""
    from cryptography.exceptions import InvalidSignature
    try:
        public_key = serialization.load_der_public_key(public_key_der)
        public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False

def aes_gcm_encrypt(key: bytes, plaintext: bytes, aad: bytes = b"") -> tuple[bytes, bytes]:
    """
    Returns (nonce, ciphertext_with_tag).
    key must be 32 bytes. aad is additional authenticated data (e.g. packet header).
    The 16-byte GCM tag is appended to ciphertext by the library automatically.
    """
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, aad)
    return nonce, ciphertext

def aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext_with_tag: bytes, aad: bytes = b"") -> bytes:
    """
    Returns plaintext. Raises cryptography.exceptions.InvalidTag on authentication failure.
    Caller must catch InvalidTag and drop the packet — never silently ignore it.
    """
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext_with_tag, aad)
