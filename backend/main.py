from __future__ import annotations

import argparse
import json
from pathlib import Path

import uvicorn

from hybrid_vpn.agent import AgentService
from hybrid_vpn.api import create_agent_app, create_gateway_app
from hybrid_vpn.config import AgentConfig, GatewayConfig
from hybrid_vpn.crypto.hybrid import run_demo_handshake
from hybrid_vpn.gateway import GatewayService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hybrid VPN scaffold runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    agent_api = subparsers.add_parser("agent-api", help="Run the local agent control API")
    agent_api.add_argument("--host", default="127.0.0.1")
    agent_api.add_argument("--port", type=int, default=8765)
    agent_api.add_argument("--gateway-url", default=None, help="Gateway API URL (e.g. http://10.0.2.15:9876)")
    agent_api.add_argument("--reload", action="store_true")

    gateway_api = subparsers.add_parser("gateway-api", help="Run the gateway control API")
    gateway_api.add_argument("--host", default="0.0.0.0")
    gateway_api.add_argument("--port", type=int, default=9876)
    gateway_api.add_argument("--reload", action="store_true")

    subparsers.add_parser("demo-handshake", help="Run the phase-1 hybrid handshake demo")
    subparsers.add_parser("print-config", help="Print default runtime configuration")
    return parser


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
        config = AgentConfig(control_host=args.host, control_port=args.port)
        agent = AgentService(config)
        app = create_agent_app(agent, gateway_url=args.gateway_url)
        uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
        return

    if args.command == "gateway-api":
        config = GatewayConfig(listen_host=args.host, listen_port=args.port)
        gateway = GatewayService(config)
        app = create_gateway_app(gateway)
        uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
        return

    parser.error(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
