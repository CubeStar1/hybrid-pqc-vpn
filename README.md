# Hybrid Post-Quantum VPN Backend

A prototype VPN backend implementing a hybrid cryptographic handshake (X25519 + ML-KEM-768) and authenticated encryption (AES-256-GCM).

## Features
- **Hybrid Key Exchange**: Combines Elliptic Curve Diffie-Hellman (X25519) with ML-KEM-768 for quantum resistance.
- **Hybrid Authentication**: Parallel signatures using ECDSA-P256 and ML-DSA-65.
- **FastAPI Interface**: Clean REST API for session management and benchmarking.
- **Linux TUN Support**: Real-world tunnel I/O via standard TUN interfaces.

## Installation

### Prerequisites (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y liboqs-dev cmake build-essential libssl-dev python3-dev
```

### Python Setup
```bash
pip install -r requirements.txt
```

## Usage

### 1. Configure TUN Interface
```bash
sudo ./scripts/setup_tun.sh vpn0 10.8.0.1
```

### 2. Run Server
```bash
python scripts/run_server.py
```

### 3. Run Benchmarks
```bash
python scripts/benchmark.py --iterations 50
```

## Testing
```bash
pytest tests/ -v
```
