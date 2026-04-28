import uuid
from vpn.handshake.initiator import HandshakeInitiator
from vpn.handshake.responder import HandshakeResponder
from vpn.session.store import SessionState, session_store
from vpn.config import config

class SessionManager:
    """
    Orchestrates full handshakes and stores resulting sessions.
    
    For a local simulation (both sides in-process):
        manager = SessionManager()
        session_id = await manager.local_handshake()
    
    For real network use, call initiator/responder methods separately
    with the raw bytes flowing over a socket.
    """

    async def local_handshake(self, peer_address: str = "local") -> str:
        """
        Runs a complete initiator+responder handshake in-process.
        Used for testing and benchmarking. Returns session_id.
        """
        initiator = HandshakeInitiator()
        responder = HandshakeResponder()

        hello = initiator.create_hello()
        response = responder.process_hello(hello)
        finish = initiator.process_response(response)
        responder.process_finish(finish)

        # Both should now have identical session keys
        assert initiator.session_keys["enc_key"] == responder.session_keys["enc_key"], \
            "CRITICAL: Key mismatch after handshake"

        session = SessionState(
            session_id=initiator.session_id,
            enc_key=initiator.session_keys["enc_key"],
            mac_key=initiator.session_keys["mac_key"],
            selected_suite=initiator.selected_suite,
            peer_address=peer_address,
        )
        await session_store.create(session)
        return initiator.session_id

    async def disconnect(self, session_id: str) -> bool:
        return await session_store.delete(session_id)

    async def get_session(self, session_id: str) -> SessionState | None:
        return await session_store.get(session_id)

    async def list_sessions(self) -> list[SessionState]:
        return await session_store.list_all()

    async def cleanup_expired(self) -> list[str]:
        return await session_store.expire_old(config.session_timeout_seconds)

session_manager = SessionManager()
