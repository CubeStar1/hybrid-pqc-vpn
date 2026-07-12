# Hybrid VPN Architecture Diagram
## Main layout

Use 4 grouped areas:

- `Client Controller`
- `Client Runtime`
- `Gateway Runtime`
- `Deployment`

Add a top banner:

`Hybrid VPN Control Plane + Tunnel Data Plane`

## Blocks

### Client Controller

#### Electron + Next.js Desktop App

Content:

- User dashboard
- Connect / disconnect VPN
- Show status and session info
- View architecture and handshake flow

#### Electron Host

Content:

- Hosts desktop app
- Provides runtime context
- Starts packaged frontend

### Client Runtime

#### FastAPI Agent API

Content:

- Local control API
- Status and profile endpoints
- Connect / disconnect requests

Label:

- `HTTP :8765`

#### Agent Service

Content:

- Authentication and session control
- Hybrid handshake
- Tunnel startup

#### Client Tunnel

Content:

- Linux TUN interface `hyb0`
- Encrypted UDP transport
- Route traffic through VPN

Label:

- `UDP :4434`

### Gateway Runtime

#### FastAPI Gateway API

Content:

- Remote control API
- Auth and handshake endpoints
- Session start / stop

Label:

- `HTTP :9876`

#### Gateway Service

Content:

- Verify credentials
- Process hybrid handshake
- Manage remote session

#### Gateway Tunnel

Content:

- Linux TUN interface `hyb-gw0`
- Encrypted UDP endpoint
- Forward VPN traffic

Label:

- `UDP :4433`

#### Gateway Network

Content:

- IP forwarding
- NAT with `iptables`
- Internet access for client traffic

### Deployment

#### Linux Environment

Content:

- Required for real tunnel execution

#### Docker

Content:

- Backend API packaging

#### Electron App

Content:

- Desktop distribution

## Connections

Keep only these arrows:

- `User` -> `Electron + Next.js Desktop App`
- `Electron App` -> `FastAPI Agent API`
  - `HTTP control`

- `FastAPI Agent API` -> `Agent Service`
- `Agent Service` -> `FastAPI Gateway API`
  - `Auth + Handshake + Session`

- `FastAPI Gateway API` -> `Gateway Service`
- `Agent Service` -> `Client Tunnel`
- `Gateway Service` -> `Gateway Tunnel`

- `Client Tunnel` <-> `Gateway Tunnel`
  - `Encrypted UDP tunnel`

- `Gateway Tunnel` -> `Gateway Network`
- `Gateway Network` -> `Internet`

## Tech stack

### Frontend

- Electron
- Next.js
- React
- TypeScript
- Tailwind CSS

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- HTTPX

### Crypto and networking

- X25519
- ML-KEM-768
- ECDSA P-256
- AES-256-GCM
- Linux TUN
- `pyroute2`
- `iptables`

### Packaging

- Docker
- Electron Builder
- uv
- pnpm

## Suggested final diagram style

To avoid clutter, keep these rules:

- Only 1 to 3 bullets per box
- No code paths or endpoint lists inside the image
- No config block

- Keep arrow labels very short
- Show only one user icon and one internet icon

## Revised prompt for image generation

```text
Create a clean architecture diagram for a hybrid post-quantum VPN project.

Use 4 grouped sections: Client Controller, Client Runtime, Gateway Runtime, Deployment.

Important style rules:
- Use bullet points only, never numbered lists like (1), 1., or 1)
- Keep each box to 2 or 3 short bullet points
- Include a small dashboard screenshot or UI mockup inside the Client Controller section
- Use short arrow labels only
- Keep the layout spacious and not cluttered
- Use polished academic/system-design styling similar to a modern thesis or capstone architecture figure

Client Controller contains:
- Electron + Next.js Desktop App
- Electron Host

For the Client Controller section:
- Show a small embedded preview image of the desktop dashboard
- Place the preview near the "Electron + Next.js Desktop App" block
- The preview should look like a real admin/control dashboard screenshot, not an icon

Client Runtime contains:
- FastAPI Agent API (HTTP 8765)
- Agent Service
- Client Tunnel (hyb0, UDP 4434)

Gateway Runtime contains:
- FastAPI Gateway API (HTTP 9876)
- Gateway Service
- Gateway Tunnel (hyb-gw0, UDP 4433)
- Gateway Network

Deployment contains:
- Linux Environment
- Docker
- Electron App

Connections:
- User to Desktop App
- Desktop App to Agent API over HTTP
- Agent API to Agent Service
- Agent Service to Gateway API for auth, handshake, and session control
- Gateway API to Gateway Service
- Agent Service to Client Tunnel
- Gateway Service to Gateway Tunnel
- Client Tunnel to Gateway Tunnel over encrypted UDP
- Gateway Tunnel to Gateway Network
- Gateway Network to Internet

Tech stack footer:
- Frontend: Electron, Next.js, React, TypeScript, Tailwind CSS
- Backend: Python, FastAPI, Uvicorn, Pydantic, HTTPX
- Crypto/Network: X25519, ML-KEM-768, ECDSA P-256, AES-256-GCM, Linux TUN, pyroute2, iptables
- Packaging: Docker, Electron Builder, uv, pnpm

Text inside boxes:
- Use normal round bullet points
- Do not prefix bullet points with numbers
- Do not write long sentences
- Prefer phrases like "Local control API", "Hybrid handshake", "Encrypted UDP tunnel"

Visual extras:
- Keep technology logos in a footer strip
- Keep one user icon on the left
- Keep one internet/cloud icon on the right
- Use soft color-coded grouped containers
- Preserve generous spacing between blocks
```
