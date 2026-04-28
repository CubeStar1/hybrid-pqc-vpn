from fastapi.middleware.cors import CORSMiddleware
from vpn.config import config

def add_middleware(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
