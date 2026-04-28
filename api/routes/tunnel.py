from fastapi import APIRouter, HTTPException
from api.schemas.models import (
    ConnectRequest, ConnectResponse,
    DisconnectRequest, DisconnectResponse,
    ServerStatus
)
from vpn.session.manager import session_manager
from vpn.config import config
import time

router = APIRouter(prefix="/tunnel", tags=["tunnel"])

@router.post("/connect", response_model=ConnectResponse)
async def connect(req: ConnectRequest):
    """
    Runs a full hybrid handshake and creates a new session.
    Returns the session_id and metadata.
    """
    try:
        session_id = await session_manager.local_handshake(
            peer_address=req.peer_address or "local"
        )
        session = await session_manager.get_session(session_id)
        return ConnectResponse(
            session_id=session_id,
            selected_suite=session.selected_suite,
            enc_key_hex=session.enc_key.hex(),
            created_at=session.created_at,
            message="Hybrid handshake completed successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/disconnect", response_model=DisconnectResponse)
async def disconnect(req: DisconnectRequest):
    success = await session_manager.disconnect(req.session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return DisconnectResponse(session_id=req.session_id, success=True)

@router.get("/status", response_model=ServerStatus)
async def status():
    sessions = await session_manager.list_sessions()
    return ServerStatus(
        status="running",
        active_sessions=len(sessions),
        supported_suites=config.supported_algo_suites
    )
