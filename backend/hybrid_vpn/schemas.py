"""Pydantic schemas for the control API."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


# ── Phase / status ───────────────────────────────────────────────────


class PhaseStatus(BaseModel):
    name: str
    status: Literal["complete", "in_progress", "planned"]
    summary: str


class ArchitectureCard(BaseModel):
    title: str
    description: str
    details: list[str]


# ── Profiles ─────────────────────────────────────────────────────────


class AgentProfileSummary(BaseModel):
    id: str
    name: str
    gateway_host: str
    gateway_port: int
    tunnel_cidr: str
    mtu: int
    supported_suite: str


# ── Runtime ──────────────────────────────────────────────────────────


class RuntimeContext(BaseModel):
    mode: Literal["agent", "gateway"]
    platform: str
    linux_vm_target: bool
    tun_interface: str | None = None
    control_api: str | None = None
    notes: list[str] = Field(default_factory=list)


class TunnelStatus(BaseModel):
    active: bool = False
    tun_device: str | None = None
    local_address: str | None = None
    remote_endpoint: str | None = None
    packets_sent: int = 0
    packets_recv: int = 0
    bytes_sent: int = 0
    bytes_recv: int = 0


class SessionSummary(BaseModel):
    session_id: str
    state: Literal["idle", "connecting", "connected", "disconnected", "error"]
    profile_id: str
    username: str
    suite: str
    transcript_hash_hex: str | None = None
    pqc_enabled: bool = False
    connected_at: datetime = Field(default_factory=utc_now)
    tunnel: TunnelStatus = Field(default_factory=TunnelStatus)
    notes: list[str] = Field(default_factory=list)


class RuntimeStatus(BaseModel):
    service: str
    version: str
    runtime: RuntimeContext
    phases: list[PhaseStatus]
    current_session: SessionSummary | None = None
    oqs_available: bool
    server_identity_ready: bool
    updated_at: datetime = Field(default_factory=utc_now)


# ── Requests / responses ─────────────────────────────────────────────


class ConnectRequest(BaseModel):
    profile_id: str
    username: str
    password: str


class DisconnectRequest(BaseModel):
    reason: str = "user-request"


class DisconnectResponse(BaseModel):
    disconnected: bool
    message: str


class ConnectResponse(BaseModel):
    accepted: bool
    message: str
    session: SessionSummary | None = None


# ── Handshake protocol messages ──────────────────────────────────────


class ClientHelloMessage(BaseModel):
    suite: str
    x25519_public_hex: str
    mlkem_public_hex: str | None = None


class ServerHelloMessage(BaseModel):
    x25519_public_hex: str
    mlkem_ciphertext_hex: str | None = None
    ecdsa_signature_hex: str
    ecdsa_public_key_der_hex: str
    transcript_hash_hex: str


# ── Project snapshot ─────────────────────────────────────────────────


class ProjectSnapshot(BaseModel):
    title: str
    summary: str
    architecture: list[ArchitectureCard]
    phases: list[PhaseStatus]
