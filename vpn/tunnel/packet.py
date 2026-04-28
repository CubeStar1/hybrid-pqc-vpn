import struct
from vpn.crypto.classical import aes_gcm_encrypt, aes_gcm_decrypt

HEADER_FORMAT = "!16sQ"   # 16 bytes session_id + 8 bytes uint64 seq_no = 24 bytes
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # 24
NONCE_SIZE = 12

def build_packet(
    session_id_bytes: bytes,   # exactly 16 bytes (uuid.bytes)
    seq_no: int,
    enc_key: bytes,
    plaintext: bytes
) -> bytes:
    """
    Encrypts plaintext and returns a complete wire packet.
    Raises ValueError if session_id_bytes is not exactly 16 bytes.
    """
    if len(session_id_bytes) != 16:
        raise ValueError("session_id_bytes must be 16 bytes")

    header = struct.pack(HEADER_FORMAT, session_id_bytes, seq_no)
    nonce, ciphertext = aes_gcm_encrypt(enc_key, plaintext, aad=header)
    return header + nonce + ciphertext


def parse_packet(packet: bytes, enc_key: bytes) -> tuple[bytes, int, bytes]:
    """
    Parses and decrypts a wire packet.
    Returns (session_id_bytes, seq_no, plaintext).
    Raises struct.error on malformed header, cryptography.exceptions.InvalidTag on bad auth.
    """
    header = packet[:HEADER_SIZE]
    session_id_bytes, seq_no = struct.unpack(HEADER_FORMAT, header)
    nonce = packet[HEADER_SIZE: HEADER_SIZE + NONCE_SIZE]
    ciphertext = packet[HEADER_SIZE + NONCE_SIZE:]
    plaintext = aes_gcm_decrypt(enc_key, nonce, ciphertext, aad=header)
    return session_id_bytes, seq_no, plaintext
