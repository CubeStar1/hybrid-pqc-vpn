# Hybrid VPN Implementation Plan

## Summary

- Build the project as a Linux VM-based prototype where both the Electron desktop client and the Python tunnel engine live inside Linux.
- Phases 1–4 are fully implemented: hybrid crypto harness, encrypted UDP tunnel, TUN device management, and Electron desktop integration.
- Keep the initial design research-grade and explicit about what is MVP versus what is still staged.

## Architecture

### Client VM

- Electron + Next.js desktop shell for profile selection, authentication, connect/disconnect, logs, and performance views.
- Local Python agent exposing a loopback control API (`:8765`) for the desktop app.
- TUN device (`hyb0`) with `pyroute2` for IP assignment and route management.
- Encrypted UDP transport (`:4434`) with AES-256-GCM and sequence-number replay protection.

### Gateway VM

- Python gateway control service for authentication, session policy, and handshake processing.
- Pinned `ECDSA-P256` server authentication.
- TUN device (`hyb-gw0`) and UDP listener (`:4433`) for the data plane.
- `ML-DSA-65` planned after the control plane and tunnel path are stable.

### Hybrid Control Plane

- Active MVP suite: `X25519MLKEM768_AES256GCM_ECDSA_P256`.
- Real single-round client-server handshake protocol over HTTP.
- Transcript-bound `HKDF-SHA256` key schedule with the `ML-KEM-768` shared secret concatenated before the `X25519` shared secret.
- `AES-256-GCM` used for the tunnel packet data plane.

## Delivery Phases

1. Phase 1 ✅: Hybrid crypto harness — X25519, ML-KEM-768, transcript hashing, HKDF key derivation, ECDSA-P256 authentication.
2. Phase 2 ✅: UDP framing — AES-256-GCM encrypted datagrams with sequence-number nonces and replay protection.
3. Phase 3 ✅: Linux TUN — device creation via `/dev/net/tun`, IP/route management via `pyroute2`, clean teardown.
4. Phase 4 ✅: Electron integration — desktop dashboard connected to agent API with browser-mode fallback.
5. Phase 5 📋: Experiment dashboards, performance capture, and report/demo outputs.
6. Phase 6 📋: Dual-signature authentication with `ECDSA-P256 + ML-DSA-65`.

## Current Implementation Status

- Implemented:
  - Python package with agent, gateway, config, schemas, and FastAPI control APIs.
  - Real client-server hybrid handshake protocol (HandshakeClient/HandshakeServer).
  - TUN device management with `pyroute2` IP/route configuration.
  - Encrypted UDP tunnel with AES-256-GCM, sequence numbers, and replay protection.
  - TunnelManager orchestrating TUN ↔ UDP forwarding in background threads.
  - Electron preload/main-process runtime bridge for the desktop dashboard.
  - Next.js control dashboard with browser-mode fallback for development.
  - CORS-enabled APIs for seamless frontend-backend communication.
- Not implemented yet:
  - ML-DSA-65 authentication.
  - Experiment dashboards and performance metrics.

## Linux VM Workflow

- Preferred topology:
  - VM 1: client desktop + agent.
  - VM 2: gateway service.
- Hypervisors:
  - VMware Workstation preferred.
  - VirtualBox acceptable.
  - Hyper-V acceptable if it fits your setup better.
- Initial networking:
  - Use bridged mode for VM-to-VM communication.
  - NAT acceptable for single-VM testing.
  - All VPN routing logic stays inside the Linux guests.

## Validation Targets

- Successful real handshake between agent and gateway with authenticated transcript.
- Clear failure path when PQC support is unavailable.
- Agent control API reachable from the desktop app (Electron or browser).
- Profile selection, connect/disconnect, and session state visible in the UI.
- TUN device creation and encrypted UDP forwarding on Linux.
- Future milestones: rekeying, classical-vs-hybrid benchmark capture.
