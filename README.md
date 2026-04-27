# Hybrid Post-Quantum VPN

A research-grade VPN prototype combining classical (X25519, ECDSA-P256) and post-quantum (ML-KEM-768) cryptography with an Electron + Next.js desktop controller.

## Architecture

```
┌──────────────────────────────────┐      ┌────────────────────────────┐
│  VM 1 — Client                   │      │  VM 2 — Gateway            │
│  ┌────────────────────────────┐  │      │  ┌──────────────────────┐  │
│  │  Electron + Next.js        │  │      │  │  Gateway API         │  │
│  │  (Desktop Dashboard)       │  │      │  │  python main.py      │  │
│  │        ↕ HTTP :8765        │  │      │  │   gateway-api        │  │
│  │  Python Agent API          │  │      │  │  HTTP :9876           │  │
│  │  python main.py agent-api  │  │      │  │  UDP  :4433          │  │
│  │        ↕ TUN hyb0          │  │      │  │        ↕ TUN hyb-gw0 │  │
│  │  UDP :4434 ←──────────────────────────→ │  UDP :4433           │  │
│  └────────────────────────────┘  │      │  └──────────────────────┘  │
│  Ubuntu 22.04/24.04              │      │  Ubuntu 22.04/24.04        │
└──────────────────────────────────┘      └────────────────────────────┘
```

## Implemented Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Hybrid crypto harness: X25519 + ML-KEM-768 + HKDF + ECDSA-P256 | ✅ Complete |
| 2 | UDP framing with AES-256-GCM encryption + replay protection | ✅ Complete |
| 3 | Linux TUN device creation + IP/route management via pyroute2 | ✅ Complete |
| 4 | Electron + Next.js desktop dashboard ↔ Agent API | ✅ Complete |
| 5 | Experiment dashboards + performance capture | 📋 Planned |
| 6 | Dual-signature auth (ECDSA + ML-DSA-65) | 📋 Planned |

## Quick Start

### Prerequisites

- **Linux** (Ubuntu 22.04/24.04) — required for TUN + UDP tunnel
- **Python 3.12+** and **[uv](https://docs.astral.sh/uv/)**
- **Node.js 20+** and **pnpm**
- **liboqs** (for ML-KEM-768 support)

### 1. Install system dependencies

```bash
sudo apt update && sudo apt install -y \
  build-essential cmake ninja-build git curl \
  python3.12 python3.12-venv python3-pip \
  libssl-dev \
  libnss3 libatk-bridge2.0-0 libgtk-3-0 libgbm1 xdg-utils

# uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node.js 20+ via NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
npm install -g pnpm
```

### 2. Install liboqs (for ML-KEM-768)

```bash
cd /tmp
git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git
cd liboqs && mkdir build && cd build
cmake -GNinja -DBUILD_SHARED_LIBS=ON -DCMAKE_INSTALL_PREFIX=/usr/local ..
ninja && sudo ninja install
sudo ldconfig

# Verify the shared library exists for liboqs-python
ls /usr/local/lib/liboqs.so*
```

### 3. Set up and run the backend

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Verify crypto works
cd backend
uv sync --all-extras
uv run python main.py demo-handshake

# Same-machine testing: backend/.env defaults to localhost

# Run the gateway API
uv run python main.py gateway-api

# Run the agent API
uv run python main.py agent-api
```

### 4. Set up and run the frontend

```bash
cd frontend
pnpm install
cp .env.example .env

# Browser-only dev (no Electron)
pnpm next:dev

# Full Electron + Next.js dev mode
pnpm dev
```

### 5. Verify with curl

```bash
# Health check
curl http://127.0.0.1:8765/health

# Agent status
curl http://127.0.0.1:8765/status | uv run python -m json.tool

# Demo handshake
curl -X POST http://127.0.0.1:8765/demo/handshake | uv run python -m json.tool

# Connect
curl -X POST http://127.0.0.1:8765/connect \
  -H "Content-Type: application/json" \
  -d '{"profile_id":"lab-gateway","username":"demo","password":"demo-vpn-2026"}'

# Disconnect
curl -X POST http://127.0.0.1:8765/disconnect \
  -H "Content-Type: application/json" \
  -d '{"reason":"test"}'
```

## Linux VM Setup (VMware Workstation)

### Create VMs

- **Guest OS**: Ubuntu 22.04/24.04 LTS
- **RAM**: ≥ 4 GB (8 GB recommended for Electron)
- **Disk**: ≥ 30 GB
- **Network**: NAT or Bridged
- **Enable 3D acceleration** for Electron rendering

### Networking

| VM | Role | IP (example) | Services |
|----|------|--------------|----------|
| VM 1 | Client + Agent | 192.168.x.10 | Agent API :8765, UDP :4434 |
| VM 2 | Gateway | 192.168.x.20 | Gateway API :9876, UDP :4433 |

Use bridged networking for VM-to-VM communication, or NAT with port forwarding.
For VM-based testing, update `backend/.env` so `HYBRID_VPN_AGENT_GATEWAY_URL` and
`HYBRID_VPN_AGENT_GATEWAY_HOST` point at the gateway VM.
Update `frontend/.env` so `NEXT_PUBLIC_HYBRID_VPN_AGENT_API_URL` points at the agent VM and
`NEXT_PUBLIC_HYBRID_VPN_GATEWAY_API_URL` points at the gateway VM.

### Running the full tunnel (requires root)

```bash
# On Gateway VM
sudo uv run python main.py gateway-api

# On Client VM
HYBRID_VPN_AGENT_GATEWAY_URL=http://192.168.x.20:9876 \
HYBRID_VPN_AGENT_GATEWAY_HOST=192.168.x.20 \
sudo uv run python main.py agent-api
```

Root/sudo is needed for TUN device creation. After connecting through the dashboard,
the agent creates `hyb0` (10.42.0.2/24) and the gateway creates `hyb-gw0` (10.42.0.1/24).

### Localhost backend testing

To run both services on the same Linux machine in separate terminals:

```bash
cd backend
cp .env.example .env

# terminal 1
uv run python main.py gateway-api

# terminal 2
uv run python main.py agent-api
```

That supports health, status, auth, and handshake immediately. Full TUN tunnel testing on
one machine still requires `sudo` because the agent creates `hyb0`.

## Development (Windows/macOS)

The backend runs on Windows/macOS in limited mode:
- **Crypto handshake**: ✅ works (PQC unavailable without liboqs)
- **TUN + UDP tunnel**: ❌ skipped (Linux only)
- **Frontend**: ✅ fully functional in browser mode

```powershell
# Backend
cd backend
uv sync --all-extras
uv run python main.py agent-api

# Frontend
cd frontend
pnpm install
pnpm next:dev
```

## Running Tests

```bash
cd backend
uv run pytest tests/ -v
```

## Project Structure

```
├── backend/
│   ├── hybrid_vpn/
│   │   ├── crypto/
│   │   │   ├── classical.py   # X25519, ECDSA, HKDF, AES-GCM
│   │   │   ├── hybrid.py      # Hybrid handshake protocol + demo
│   │   │   └── pqc.py         # ML-KEM-768 via liboqs
│   │   ├── agent.py           # Agent service (connect/disconnect/status)
│   │   ├── api.py             # FastAPI apps (agent + gateway)
│   │   ├── config.py          # Pydantic config models
│   │   ├── gateway.py         # Gateway service (auth/handshake)
│   │   ├── schemas.py         # Request/response models
│   │   └── tunnel.py          # TUN device + UDP transport
│   ├── tests/
│   ├── main.py                # CLI entry point
│   └── pyproject.toml
├── frontend/
│   ├── electron/src/          # Electron main + preload
│   ├── src/
│   │   ├── app/               # Next.js pages
│   │   └── components/
│   │       └── vpn-dashboard/ # Dashboard UI
│   └── package.json
└── docs/
    └── IMPLEMENTATION_PLAN.md
```
