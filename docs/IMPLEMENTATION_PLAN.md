# Hybrid VPN Implementation Plan

## Summary

- Build the project as a Linux VM-based prototype where both the Electron desktop client and the Python tunnel engine live inside Linux.
- Treat the current repository as a phased implementation: the control plane, crypto harness, and desktop controller are now scaffolded; live UDP tunneling and TUN routing are next.
- Keep the initial design research-grade and explicit about what is MVP versus what is still staged.

## Architecture

### Client VM

- Electron + Next.js desktop shell for profile selection, authentication, connect/disconnect, logs, and performance views.
- Local Python agent exposing a loopback control API for the desktop app.
- Linux-only tunnel target with `/dev/net/tun`, `pyroute2`, and `systemd` reserved for the live data-plane milestone.

### Gateway VM

- Python gateway control service for authentication, session policy, and tunnel lifecycle.
- Pinned `ECDSA-P256` server authentication in MVP.
- `ML-DSA-65` planned after the control plane and tunnel path are stable.

### Hybrid Control Plane

- Active MVP suite: `X25519MLKEM768_AES256GCM_ECDSA_P256`.
- Transcript-bound `HKDF-SHA256` key schedule with the `ML-KEM-768` shared secret concatenated before the `X25519` shared secret.
- `AES-256-GCM` retained as the tunnel cipher for the upcoming packet data plane.

## Delivery Phases

1. Phase 1: hybrid crypto harness for `X25519`, `ML-KEM-768`, transcript hashing, and key derivation.
2. Phase 2: UDP framing and encrypted control/data packet transport.
3. Phase 3: Linux TUN creation, route management, and teardown.
4. Phase 4: Electron integration with the local agent API and runtime surface.
5. Phase 5: experiment dashboards, performance capture, and report/demo outputs.
6. Phase 6: dual-signature authentication with `ECDSA-P256 + ML-DSA-65`.

## Current Implementation Status

- Implemented now:
  - Python package scaffold for the agent, gateway, config, schemas, and FastAPI control API.
  - Hybrid handshake demo harness using `cryptography` and optional `liboqs-python`.
  - Electron preload/main-process runtime bridge for the desktop dashboard.
  - Next.js control dashboard that reflects Linux VM assumptions and tries the local agent API.
- Not implemented yet:
  - Live UDP packet transport.
  - Real TUN creation and route mutation.
  - Full gateway-to-client tunnel traffic.
  - ML-DSA-65 authentication.

## Linux VM Workflow

- Preferred topology:
  - VM 1: client desktop + agent.
  - VM 2: gateway service or a separate Linux host/cloud VM.
- Hypervisors:
  - VMware Workstation preferred.
  - VirtualBox acceptable.
  - Hyper-V acceptable if it fits your setup better.
- Initial networking:
  - Use NAT or bridged mode for base reachability.
  - Keep all VPN routing logic inside the Linux guests.

## Validation Targets

- Successful handshake demo with authenticated transcript.
- Clear failure path when PQC support is unavailable.
- Agent control API reachable from the desktop app.
- Profile selection, connect/disconnect, and session state visible in the UI.
- Future milestones: replay protection, rekeying, packet transport, and classical-vs-hybrid benchmark capture.
