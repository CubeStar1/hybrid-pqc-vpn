"""FastAPI application factory for agent and gateway control APIs."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

from .agent import AgentService
from .config import RuntimeMode
from .crypto.hybrid import run_demo_handshake
from .gateway import GatewayService
from .schemas import (
    ClientHelloMessage,
    ConnectRequest,
    DisconnectRequest,
    GatewaySessionStartRequest,
    GatewaySessionStopRequest,
)


def _add_cors(app: FastAPI) -> None:
    """Allow the Electron renderer and browser dev server to call the API."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ── Agent API ────────────────────────────────────────────────────────


def create_agent_app(agent: AgentService, gateway_url: str | None = None) -> FastAPI:
    app = FastAPI(
        title="Hybrid VPN Agent API",
        version="0.1.0",
        summary="Local control API for the RVCE hybrid VPN agent.",
    )
    _add_cors(app)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "agent"}

    @app.get("/status")
    def get_status():
        return agent.status()

    @app.get("/profiles")
    def get_profiles():
        return agent.profiles()

    @app.post("/demo/handshake")
    def demo_handshake():
        return run_demo_handshake()

    @app.post("/connect")
    def connect(request: ConnectRequest):
        return agent.connect(request, gateway_url=gateway_url)

    @app.post("/disconnect")
    def disconnect(request: DisconnectRequest):
        return agent.disconnect(request.reason)

    @app.get("/runtime-mode")
    def runtime_mode():
        return {"mode": RuntimeMode.AGENT.value}

    return app


# ── Gateway API ──────────────────────────────────────────────────────


def create_gateway_app(gateway: GatewayService) -> FastAPI:
    app = FastAPI(
        title="Hybrid VPN Gateway API",
        version="0.1.0",
        summary="Gateway control API for the RVCE hybrid VPN.",
    )
    _add_cors(app)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "gateway"}

    @app.get("/status")
    def get_status():
        return gateway.status()

    @app.post("/auth")
    def authenticate(payload: dict):
        ok = gateway.authenticate(payload.get("username", ""), payload.get("password", ""))
        return {"authenticated": ok}

    @app.post("/handshake")
    def handshake(client_hello: ClientHelloMessage):
        return gateway.perform_handshake(client_hello)

    @app.post("/session/start")
    def start_session(payload: GatewaySessionStartRequest, request: Request):
        client_host = request.client.host if request.client else None
        if not client_host:
            return {"accepted": False, "message": "Could not determine client source address."}
        return gateway.start_session(
            username=payload.username,
            profile_id=payload.profile_id,
            client_addr=(client_host, payload.client_udp_port),
        )

    @app.post("/session/stop")
    def stop_session(payload: GatewaySessionStopRequest):
        return gateway.stop_session(payload.reason)

    @app.get("/runtime-mode")
    def runtime_mode():
        return {"mode": RuntimeMode.GATEWAY.value}

    return app
