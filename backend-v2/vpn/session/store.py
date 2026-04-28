import asyncio
from dataclasses import dataclass, field
from typing import Optional
import time

@dataclass
class SessionState:
    session_id: str
    enc_key: bytes
    mac_key: bytes
    selected_suite: str
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    packets_sent: int = 0
    packets_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    rekey_count: int = 0
    peer_address: Optional[str] = None

class SessionStore:
    def __init__(self):
        self._sessions: dict[str, SessionState] = {}
        self._lock = asyncio.Lock()

    async def create(self, state: SessionState) -> None:
        async with self._lock:
            self._sessions[state.session_id] = state

    async def get(self, session_id: str) -> Optional[SessionState]:
        async with self._lock:
            return self._sessions.get(session_id)

    async def update(self, session_id: str, **kwargs) -> None:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                for k, v in kwargs.items():
                    setattr(session, k, v)
                session.last_active = time.time()

    async def delete(self, session_id: str) -> bool:
        async with self._lock:
            return self._sessions.pop(session_id, None) is not None

    async def list_all(self) -> list[SessionState]:
        async with self._lock:
            return list(self._sessions.values())

    async def expire_old(self, timeout_seconds: int) -> list[str]:
        """Removes and returns IDs of sessions inactive for longer than timeout_seconds."""
        now = time.time()
        async with self._lock:
            expired = [
                sid for sid, s in self._sessions.items()
                if now - s.last_active > timeout_seconds
            ]
            for sid in expired:
                del self._sessions[sid]
        return expired

# Singleton
session_store = SessionStore()
