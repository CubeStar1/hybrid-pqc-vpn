# Hybrid VPN Backend

This backend now contains the first implementation scaffold for the Linux VM-based hybrid VPN:

- `hybrid_vpn.agent`: local client-agent control logic
- `hybrid_vpn.gateway`: server-side auth and session scaffolding
- `hybrid_vpn.crypto`: phase-1 hybrid handshake and key schedule helpers
- `hybrid_vpn.api`: FastAPI control surface for the Electron app or curl

## Suggested commands

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python main.py print-config
python main.py demo-handshake
python main.py agent-api --host 127.0.0.1 --port 8765
python main.py gateway-api --host 0.0.0.0 --port 9876
```

## Notes

- `liboqs-python` is required for real `ML-KEM-768` runs.
- Without a working `oqs` install, the control API still loads but the handshake demo will report PQC as unavailable.
- TUN/route orchestration is intentionally scaffolded and documented as the next milestone; the current code focuses on the control plane, crypto harness, and desktop integration path.
