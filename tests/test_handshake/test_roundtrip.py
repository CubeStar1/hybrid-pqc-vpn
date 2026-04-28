import pytest
from vpn.handshake.initiator import HandshakeInitiator
from vpn.handshake.responder import HandshakeResponder

def test_full_handshake_hybrid_keys_match():
    """
    Core correctness test: both sides must derive identical session keys.
    Any failure here means the cryptographic design is broken.
    """
    initiator = HandshakeInitiator()
    responder = HandshakeResponder()

    hello = initiator.create_hello()
    response = responder.process_hello(hello)
    finish = initiator.process_response(response)
    responder.process_finish(finish)

    assert initiator.session_keys is not None
    assert responder.session_keys is not None
    assert initiator.session_keys["enc_key"] == responder.session_keys["enc_key"], \
        "enc_key mismatch"
    assert initiator.session_keys["mac_key"] == responder.session_keys["mac_key"], \
        "mac_key mismatch"

def test_full_handshake_selected_suite_is_hybrid():
    initiator = HandshakeInitiator()
    responder = HandshakeResponder()
    hello = initiator.create_hello()
    response = responder.process_hello(hello)
    initiator.process_response(response)
    assert "MLKEM" in initiator.selected_suite

def test_tampered_response_raises():
    initiator = HandshakeInitiator()
    responder = HandshakeResponder()
    hello = initiator.create_hello()
    response_bytes = responder.process_hello(hello)
    # Flip some bytes in the signature region
    tampered = bytearray(response_bytes)
    tampered[-10] ^= 0xFF
    with pytest.raises(Exception):
        initiator.process_response(bytes(tampered))

def test_wrong_finish_mac_raises():
    initiator = HandshakeInitiator()
    responder = HandshakeResponder()
    hello = initiator.create_hello()
    response = responder.process_hello(hello)
    finish_bytes = initiator.process_response(response)
    tampered = bytearray(finish_bytes)
    tampered[-5] ^= 0xFF
    with pytest.raises(ValueError):
        responder.process_finish(bytes(tampered))
