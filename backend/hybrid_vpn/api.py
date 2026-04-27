from __future__ import annotations

from fastapi import FastAPI

from .agent import AgentService
from .config import RuntimeMode
from .crypto.hybrid import run_demo_handshake
from .gateway import GatewayService
from .schemas import ConnectRequest, DisconnectRequest


def create_app(
    agent: AgentService,
    mode: RuntimeMode,
    *,
    gateway: GatewayService | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Hybrid VPN Control API",
        version="0.1.0",
        summary="Linux VM-oriented control plane for the RVCE hybrid VPN prototype.",
    )

    @app.get("/status")
    def get_status():
        return agent.status()

    @app.get("/profiles")
    def get_profiles():
        return agent.profiles()

    @app.get("/snapshot")
    def get_snapshot():
        return agent.snapshot()

    @app.get("/architecture")
    def get_architecture():
        cards = agent.architecture()
        if gateway is not None:
            cards.extend(gateway.architecture_cards())
        return cards

    @app.post("/demo/handshake")
    def demo_handshake():
        return run_demo_handshake()

    @app.post("/connect")
    def connect(request: ConnectRequest):
        return agent.connect(request, gateway=gateway)

    @app.post("/disconnect")
    def disconnect(request: DisconnectRequest):
        return agent.disconnect(request.reason)

    @app.get("/runtime-mode")
    def runtime_mode():
        return {"mode": mode.value}

    return app
