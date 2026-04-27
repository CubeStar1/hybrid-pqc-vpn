from __future__ import annotations

import argparse
import json
from pathlib import Path

import uvicorn

from hybrid_vpn.agent import AgentService
from hybrid_vpn.api import create_app
from hybrid_vpn.config import AgentConfig, GatewayConfig, RuntimeMode
from hybrid_vpn.crypto.hybrid import run_demo_handshake
from hybrid_vpn.gateway import GatewayService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hybrid VPN scaffold runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    agent_api = subparsers.add_parser("agent-api", help="Run the local agent control API")
    agent_api.add_argument("--host", default="127.0.0.1")
    agent_api.add_argument("--port", type=int, default=8765)
    agent_api.add_argument("--reload", action="store_true")

    gateway_api = subparsers.add_parser("gateway-api", help="Run the gateway control API")
    gateway_api.add_argument("--host", default="0.0.0.0")
    gateway_api.add_argument("--port", type=int, default=9876)
    gateway_api.add_argument("--reload", action="store_true")

    subparsers.add_parser("demo-handshake", help="Run the phase-1 hybrid handshake demo")
    subparsers.add_parser("print-config", help="Print default runtime configuration")
    return parser


def run_api(mode: RuntimeMode, host: str, port: int, reload: bool) -> None:
    if mode is RuntimeMode.AGENT:
        app = create_app(AgentService(AgentConfig(control_host=host, control_port=port)), mode)
    else:
        gateway = GatewayService(GatewayConfig(listen_host=host, listen_port=port))
        app = create_app(
            AgentService(AgentConfig(control_host="127.0.0.1", control_port=8765)),
            mode,
            gateway=gateway,
        )

    uvicorn.run(app, host=host, port=port, reload=reload)


def print_config() -> None:
    payload = {
        "agent": AgentConfig().model_dump(mode="json"),
        "gateway": GatewayConfig().model_dump(mode="json"),
    }
    print(json.dumps(payload, indent=2))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "demo-handshake":
        print(json.dumps(run_demo_handshake().model_dump(mode="json"), indent=2))
        return
    if args.command == "print-config":
        print_config()
        return
    if args.command == "agent-api":
        run_api(RuntimeMode.AGENT, args.host, args.port, args.reload)
        return
    if args.command == "gateway-api":
        run_api(RuntimeMode.GATEWAY, args.host, args.port, args.reload)
        return

    parser.error(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
