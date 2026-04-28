from __future__ import annotations

from collections.abc import Iterable
from hashlib import sha256

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def generate_x25519_private_key() -> x25519.X25519PrivateKey:
    return x25519.X25519PrivateKey.generate()


def public_bytes_from_x25519(key: x25519.X25519PublicKey) -> bytes:
    return key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def derive_x25519_shared_secret(
    private_key: x25519.X25519PrivateKey,
    peer_public_key_bytes: bytes,
) -> bytes:
    peer_key = x25519.X25519PublicKey.from_public_bytes(peer_public_key_bytes)
    return private_key.exchange(peer_key)


def generate_ecdsa_private_key() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


def sign_ecdsa(private_key: ec.EllipticCurvePrivateKey, message: bytes) -> bytes:
    return private_key.sign(message, ec.ECDSA(hashes.SHA256()))


def verify_ecdsa(public_key: ec.EllipticCurvePublicKey, message: bytes, signature: bytes) -> bool:
    try:
        public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False


def transcript_hash(messages: Iterable[bytes]) -> bytes:
    digest = sha256()
    for part in messages:
        digest.update(len(part).to_bytes(4, "big"))
        digest.update(part)
    return digest.digest()


def hkdf_expand(label: bytes, key_material: bytes, salt: bytes, length: int) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=length, salt=salt, info=label).derive(key_material)


def aes_gcm_encrypt(key: bytes, nonce: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
    return AESGCM(key).encrypt(nonce, plaintext, aad)


def aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes = b"") -> bytes:
    return AESGCM(key).decrypt(nonce, ciphertext, aad)
