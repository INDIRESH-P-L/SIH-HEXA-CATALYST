"""Response models shared across modules."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ComponentState = Literal["ok", "degraded", "down", "disabled"]


class ComponentHealth(BaseModel):
    """Health of one dependency."""

    status: ComponentState
    detail: str | None = None
    latency_ms: int | None = None


class HealthResponse(BaseModel):
    """GET /health — every dependency the application needs, in one payload."""

    status: ComponentState = Field(description="Worst component state.")
    app: str
    env: str
    auth_mode: str
    storage_mode: str
    catalogue_provider: str
    database: ComponentHealth
    embeddings: ComponentHealth
    llm: ComponentHealth
    catalogue: ComponentHealth


class KeepaliveResponse(BaseModel):
    """GET /health/keepalive.

    Supabase pauses a free project after seven days with no API requests. This
    endpoint issues one trivial query so a scheduled ping keeps it awake.
    """

    ok: bool
    database_roundtrip_ms: int
    note: str


class MessageResponse(BaseModel):
    message: str
