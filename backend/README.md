# Hybrid VPN Backend

Control plane and tunnel engine for the Linux VM-based hybrid VPN:

- `hybrid_vpn.agent`: local client-agent with real tunnel lifecycle
- `hybrid_vpn.gateway`: server-side auth, handshake, and tunnel
- `hybrid_vpn.crypto`: hybrid handshake (X25519 + ML-KEM-768 + ECDSA-P256)
- `hybrid_vpn.tunnel`: TUN device + encrypted UDP transport
- `hybrid_vpn.api`: FastAPI control surfaces for agent and gateway

## Commands

```bash
# Install dependencies
uv sync --all-extras

# Optional: create a local config file for same-machine testing
cp .env.example .env

# Print default config
uv run python main.py print-config

# Run the handshake demo
uv run python main.py demo-handshake

# Start the gateway API (server side)
uv run python main.py gateway-api

# Start the agent API (client side)
uv run python main.py agent-api

# Or override any setting explicitly at runtime
HYBRID_VPN_AGENT_GATEWAY_URL=http://192.168.x.20:9876 uv run python main.py agent-api

# Run tests
uv run pytest tests/ -v
```

## Notes

- `liboqs-python` is required for real `ML-KEM-768` runs — needs `liboqs` C library installed on the system.
- Without a working `oqs` install, the control API still loads but reports PQC as unavailable.
- TUN/route management requires Linux with root privileges. On other platforms the tunnel is gracefully skipped.
- `backend/.env` is loaded automatically with `HYBRID_VPN_AGENT_*` and `HYBRID_VPN_GATEWAY_*` variables.
- For localhost testing, set both `HYBRID_VPN_AGENT_GATEWAY_URL` and `HYBRID_VPN_AGENT_GATEWAY_HOST` to `127.0.0.1`.
- `backend/.env.example` keeps localhost active and includes a commented two-VM template.
- CLI flags still override `.env` values when you need a one-off change.
