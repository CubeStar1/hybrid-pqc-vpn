from fastapi import FastAPI
from api.middleware import add_middleware
from api.routes import tunnel, session, metrics
import asyncio
from vpn.session.manager import session_manager
from vpn.config import config

app = FastAPI(
    title="Hybrid PQ-VPN API",
    description="Post-quantum VPN backend with X25519 + ML-KEM-768 hybrid handshake",
    version="1.0.0"
)

add_middleware(app)

app.include_router(tunnel.router)
app.include_router(session.router)
app.include_router(metrics.router)

@app.on_event("startup")
async def startup():
    # Start background task to expire old sessions every 60 seconds
    async def cleanup_loop():
        while True:
            await asyncio.sleep(60)
            expired = await session_manager.cleanup_expired()
            if expired:
                print(f"[session] Expired {len(expired)} inactive sessions")
    asyncio.create_task(cleanup_loop())

@app.get("/")
async def root():
    return {"service": "Hybrid PQ-VPN", "status": "running"}
