import time
import hmac
import hashlib
from vpn.crypto.classical import (
    x25519_generate_keypair, x25519_compute_shared_secret,
    ecdsa_generate_keypair, ecdsa_sign
)
from vpn.crypto.postquantum import (
    mlkem_encapsulate,
    mldsa_generate_keypair, mldsa_sign
)
from vpn.crypto.hybrid import derive_hybrid_session_keys, derive_classical_session_keys
from vpn.handshake.messages import (
    HandshakeHello, HandshakeResponse, HandshakeFinish,
    serialize, deserialize_hello, deserialize_finish
)
from vpn.handshake.negotiation import negotiate_suite, is_hybrid_suite
from vpn.config import config

class HandshakeResponder:
    """
    Usage:
        responder = HandshakeResponder()
        response_bytes = responder.process_hello(hello_bytes)
        # send response_bytes back to initiator, receive finish_bytes
        responder.process_finish(finish_bytes)
        session_keys = responder.session_keys
    """

    def __init__(self):
        self._x25519_priv, self._x25519_pub = x25519_generate_keypair()
        self._ecdsa_priv, self._ecdsa_pub = ecdsa_generate_keypair()
        self._mldsa_priv, self._mldsa_pub = mldsa_generate_keypair()

        self.session_id: str | None = None
        self.session_keys: dict | None = None
        self.selected_suite: str | None = None
        self._hello: HandshakeHello | None = None

    def process_hello(self, hello_bytes: bytes) -> bytes:
        """
        Parses Hello, negotiates suite, runs KEM, derives keys, returns Response bytes.
        Raises ValueError if no common suite.
        """
        hello: HandshakeHello = deserialize_hello(hello_bytes)
        self._hello = hello
        self.session_id = hello.session_id

        selected = negotiate_suite(hello.supported_suites)
        if selected is None:
            raise ValueError("No common algorithm suite with initiator")
        self.selected_suite = selected

        # X25519 DH
        x25519_ss = x25519_compute_shared_secret(self._x25519_priv, hello.x25519_public_key)

        # ML-KEM encapsulation (if hybrid)
        if is_hybrid_suite(selected):
            mlkem_ciphertext, mlkem_ss = mlkem_encapsulate(hello.mlkem_public_key)
            self.session_keys = derive_hybrid_session_keys(
                x25519_ss, mlkem_ss,
                salt=self.session_id.encode()
            )
        else:
            mlkem_ciphertext = b""
            self.session_keys = derive_classical_session_keys(
                x25519_ss, salt=self.session_id.encode()
            )

        # Build signed material and sign
        resp = HandshakeResponse(
            session_id=self.session_id,
            selected_suite=selected,
            x25519_public_key=self._x25519_pub,
            ecdsa_public_key=self._ecdsa_pub,
            mldsa_public_key=self._mldsa_pub,
            mlkem_ciphertext=mlkem_ciphertext,
            ecdsa_signature=b"",   # placeholder, set after building signed material
            mldsa_signature=b"",
            timestamp=time.time(),
        )

        signed_material = self._build_signed_material(resp)
        resp.ecdsa_signature = ecdsa_sign(self._ecdsa_priv, signed_material)
        if is_hybrid_suite(selected):
            resp.mldsa_signature = mldsa_sign(self._mldsa_priv, signed_material)

        return serialize(resp)

    def process_finish(self, finish_bytes: bytes) -> None:
        """
        Validates the initiator's MAC. Raises ValueError on failure.
        This confirms both sides derived the same session key.
        """
        finish: HandshakeFinish = deserialize_finish(finish_bytes)

        if finish.session_id != self.session_id:
            raise ValueError("Session ID mismatch in Finish")

        expected_mac = hmac.new(
            self.session_keys["mac_key"],
            b"handshake-complete" + self.session_id.encode(),
            hashlib.sha256
        ).digest()

        if not hmac.compare_digest(finish.mac, expected_mac):
            raise ValueError("Finish MAC verification failed — key mismatch")

    def _build_signed_material(self, resp: HandshakeResponse) -> bytes:
        """Must produce identical output to initiator._build_signed_material."""
        return (
            resp.session_id.encode()
            + resp.selected_suite.encode()
            + resp.x25519_public_key
            + resp.ecdsa_public_key
            + resp.mldsa_public_key
            + resp.mlkem_ciphertext
        )
