from fastapi import APIRouter, HTTPException
from api.schemas.models import SessionInfo
from vpn.session.manager import session_manager

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.get("/", response_model=list[SessionInfo])
async def list_sessions():
    sessions = await session_manager.list_sessions()
    return [SessionInfo(**s.__dict__) for s in sessions]

@router.get("/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionInfo(**session.__dict__)

@router.delete("/{session_id}")
async def delete_session(session_id: str):
    success = await session_manager.disconnect(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": session_id}
