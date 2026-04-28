import os, uuid
import pytest
from vpn.tunnel.packet import build_packet, parse_packet

def test_packet_roundtrip():
    key = os.urandom(32)
    session_id = uuid.uuid4().bytes
    seq_no = 42
    plaintext = b"IP packet payload here"

    wire = build_packet(session_id, seq_no, key, plaintext)
    recovered_sid, recovered_seq, recovered_data = parse_packet(wire, key)

    assert recovered_sid == session_id
    assert recovered_seq == seq_no
    assert recovered_data == plaintext

def test_packet_rejects_wrong_key():
    from cryptography.exceptions import InvalidTag
    key = os.urandom(32)
    wrong_key = os.urandom(32)
    wire = build_packet(uuid.uuid4().bytes, 1, key, b"data")
    with pytest.raises(InvalidTag):
        parse_packet(wire, wrong_key)

def test_packet_rejects_tampered_payload():
    from cryptography.exceptions import InvalidTag
    key = os.urandom(32)
    wire = bytearray(build_packet(uuid.uuid4().bytes, 1, key, b"data"))
    wire[-1] ^= 0xFF
    with pytest.raises(InvalidTag):
        parse_packet(bytes(wire), key)
