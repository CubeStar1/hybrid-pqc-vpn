"""Starts the FastAPI server. Run: python scripts/run_server.py"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uvicorn
from vpn.config import config

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=config.server_host,
        port=config.api_port,
        reload=False,
        log_level="info"
    )
