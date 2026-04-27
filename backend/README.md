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

# Print default config
uv run python main.py print-config

# Run the handshake demo
uv run python main.py demo-handshake

# Start the agent API (client side)
uv run python main.py agent-api --host 127.0.0.1 --port 8765 --gateway-url http://<GATEWAY_IP>:9876

# Start the gateway API (server side)
uv run python main.py gateway-api --host 0.0.0.0 --port 9876

# Run tests
uv run pytest tests/ -v
```

## Notes

- `liboqs-python` is required for real `ML-KEM-768` runs — needs `liboqs` C library installed on the system.
- Without a working `oqs` install, the control API still loads but reports PQC as unavailable.
- TUN/route management requires Linux with root privileges. On other platforms the tunnel is gracefully skipped.
- Use `--gateway-url` on the agent to enable real client-server handshake with the gateway.
