from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

def hkdf_derive(
    ikm: bytes,
    length: int,
    info: bytes = b"hybrid-vpn-v1",
    salt: bytes | None = None
) -> bytes:
    """
    Derives `length` bytes of key material from ikm.
    - ikm: raw input key material (concatenated shared secrets)
    - length: total bytes to derive (e.g. 64 for two 32-byte keys)
    - info: context label — must match on both sides
    - salt: optional random salt; use session_id bytes if available
    Returns raw bytes. Caller slices them into enc_key, mac_key etc.
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=info,
    )
    return hkdf.derive(ikm)
