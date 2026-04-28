import time
import uuid
import hmac
import hashlib
from vpn.crypto.classical import (
    x25519_generate_keypair, x25519_compute_shared_secret,
    ecdsa_generate_keypair, ecdsa_verify
)
from vpn.crypto.postquantum import (
    mlkem_generate_keypair, mlkem_decapsulate,
    mldsa_generate_keypair, mldsa_verify
)
from vpn.crypto.hybrid import derive_hybrid_session_keys, derive_classical_session_keys
from vpn.handshake.messages import (
    HandshakeHello, HandshakeResponse, HandshakeFinish,
    serialize, deserialize_response
)
from vpn.handshake.negotiation import is_hybrid_suite
from vpn.config import config

class HandshakeInitiator:
    """
    Usage:
        initiator = HandshakeInitiator()
        hello_bytes = initiator.create_hello()
        # send hello_bytes to responder, receive response_bytes back
        finish_bytes = initiator.process_response(response_bytes)
        # send finish_bytes to responder
        session_keys = initiator.session_keys  # {"enc_key": ..., "mac_key": ...}
        selected_suite = initiator.selected_suite
    """

    def __init__(self):
        self.session_id = uuid.uuid4().hex
        # Generate all keypairs upfront
        self._x25519_priv, self._x25519_pub = x25519_generate_keypair()
        self._mlkem_priv, self._mlkem_pub = mlkem_generate_keypair()
        self._ecdsa_priv, self._ecdsa_pub = ecdsa_generate_keypair()
        self._mldsa_priv, self._mldsa_pub = mldsa_generate_keypair()

        self.session_keys: dict | None = None
        self.selected_suite: str | None = None

    def create_hello(self) -> bytes:
        hello = HandshakeHello(
            session_id=self.session_id,
            supported_suites=config.supported_algo_suites,
            x25519_public_key=self._x25519_pub,
            mlkem_public_key=self._mlkem_pub,
            ecdsa_public_key=self._ecdsa_pub,
            mldsa_public_key=self._mldsa_pub,
            timestamp=time.time(),
        )
        return serialize(hello)

    def process_response(self, response_bytes: bytes) -> bytes:
        """
        Validates the HandshakeResponse, derives session keys, returns Finish bytes.
        Raises ValueError on any validation failure.
        """
        resp: HandshakeResponse = deserialize_response(response_bytes)

        if resp.session_id != self.session_id:
            raise ValueError("Session ID mismatch in response")

        # --- Verify signatures ---
        signed_material = self._build_signed_material(resp)

        if not ecdsa_verify(resp.ecdsa_public_key, signed_material, resp.ecdsa_signature):
            raise ValueError("Responder ECDSA signature invalid")

        if is_hybrid_suite(resp.selected_suite):
            if not mldsa_verify(resp.mldsa_public_key, signed_material, resp.mldsa_signature):
                raise ValueError("Responder ML-DSA signature invalid")

        # --- Key derivation ---
        x25519_ss = x25519_compute_shared_secret(self._x25519_priv, resp.x25519_public_key)

        if is_hybrid_suite(resp.selected_suite):
            mlkem_ss = mlkem_decapsulate(self._mlkem_priv, resp.mlkem_ciphertext)
            self.session_keys = derive_hybrid_session_keys(
                x25519_ss, mlkem_ss,
                salt=self.session_id.encode()
            )
        else:
            self.session_keys = derive_classical_session_keys(
                x25519_ss, salt=self.session_id.encode()
            )

        self.selected_suite = resp.selected_suite

        # --- Build Finish ---
        mac = self._compute_finish_mac()
        finish = HandshakeFinish(
            session_id=self.session_id,
            mac=mac,
            timestamp=time.time(),
        )
        return serialize(finish)

    def _build_signed_material(self, resp: HandshakeResponse) -> bytes:
        """Deterministic byte string the responder signed. Must match responder._build_signed_material."""
        return (
            resp.session_id.encode()
            + resp.selected_suite.encode()
            + resp.x25519_public_key
            + resp.ecdsa_public_key
            + resp.mldsa_public_key
            + resp.mlkem_ciphertext
        )

    def _compute_finish_mac(self) -> bytes:
        return hmac.new(
            self.session_keys["mac_key"],
            b"handshake-complete" + self.session_id.encode(),
            hashlib.sha256
        ).digest()
