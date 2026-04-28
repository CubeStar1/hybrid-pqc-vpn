from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ConnectRequest(BaseModel):
    peer_address: Optional[str] = "local"
    preferred_suite: Optional[str] = None   # if None, use server default

class ConnectResponse(BaseModel):
    session_id: str
    selected_suite: str
    enc_key_hex: str          # hex-encoded enc_key for display/debugging — strip in production
    created_at: float
    message: str

class DisconnectRequest(BaseModel):
    session_id: str

class DisconnectResponse(BaseModel):
    session_id: str
    success: bool

class SessionInfo(BaseModel):
    session_id: str
    selected_suite: str
    peer_address: Optional[str]
    created_at: float
    last_active: float
    packets_sent: int
    packets_received: int
    bytes_sent: int
    bytes_received: int
    rekey_count: int

class ServerStatus(BaseModel):
    status: str
    active_sessions: int
    supported_suites: List[str]

class HandshakeMetrics(BaseModel):
    suite: str
    iterations: int
    mean_ms: float
    std_ms: float
    min_ms: float
    max_ms: float
