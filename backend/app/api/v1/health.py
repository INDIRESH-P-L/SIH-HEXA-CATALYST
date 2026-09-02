"""System health and keep-alive.

The only unauthenticated endpoints besides /auth/*.
"""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import embeddings
from app.core.config import settings
from app.core.database import get_session
from app.core.logging import get_logger
from app.schemas.common import ComponentHealth, HealthResponse, KeepaliveResponse
from app.services.m6_catalogue.provider import get_catalogue_provider

log = get_logger(__name__)
router = APIRouter(tags=["system"])

_WORST = {"ok": 0, "disabled": 1, "degraded": 2, "down": 3}


async def _check_database(session: AsyncSession) -> ComponentHealth:
    started = time.perf_counter()
    try:
        await session.execute(text("select 1"))
        elapsed = int((time.perf_counter() - started) * 1000)
        return ComponentHealth(
            status="ok",
            detail=f"{'Supavisor transaction mode' if settings.is_transaction_pooler else 'session pool'}",
            latency_ms=elapsed,
        )
    except Exception as exc:
        return ComponentHealth(status="down", detail=str(exc)[:200])


def _check_embeddings() -> ComponentHealth:
    started = time.perf_counter()
    if embeddings.warm():
        return ComponentHealth(
            status="ok",
            detail=f"{settings.EMBED_MODEL} ({settings.EMBED_DIM} dims, in-process)",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
    return ComponentHealth(status="down", detail="embedding model failed to load")


def _check_llm() -> ComponentHealth:
    """Configuration check only — deliberately does not spend a token.

    Health must be cheap enough to poll. Whether Groq actually answers is
    proven by the audit trail of real calls, not by a probe.
    """
    if not settings.LLM_ENABLED:
        return ComponentHealth(status="disabled", detail="LLM_ENABLED=false")
    if not settings.GROQ_API_KEY.strip():
        return ComponentHealth(
            status="degraded",
            detail=(
                "No GROQ_API_KEY set. AI features return their deterministic "
                "fallbacks and the application keeps working."
            ),
        )
    return ComponentHealth(
        status="ok",
        detail=f"mcq={settings.MODEL_MCQ}, text={settings.MODEL_TEXT}",
    )


async def _check_catalogue() -> ComponentHealth:
    try:
        provider = get_catalogue_provider()
    except Exception as exc:
        return ComponentHealth(status="disabled", detail=str(exc)[:200])

    started = time.perf_counter()
    reachable = await provider.health()
    elapsed = int((time.perf_counter() - started) * 1000)
    info = provider.info()
    if reachable:
        return ComponentHealth(
            status="ok",
            detail=f"{info.provider} provider at {info.base_url}",
            latency_ms=elapsed,
        )
    return ComponentHealth(
        status="degraded",
        detail=(
            f"{info.provider} provider unreachable; catalogue reads fall back "
            "to the local mirror table"
        ),
        latency_ms=elapsed,
    )


@router.get("/health", response_model=HealthResponse, summary="Dependency health")
async def health(session: Annotated[AsyncSession, Depends(get_session)]) -> HealthResponse:
    database = await _check_database(session)
    embeds = _check_embeddings()
    llm = _check_llm()
    catalogue = await _check_catalogue()

    overall = max(
        (database.status, embeds.status, llm.status, catalogue.status),
        key=lambda s: _WORST[s],
    )
    return HealthResponse(
        status=overall,
        app=settings.APP_NAME,
        env=settings.APP_ENV,
        auth_mode=settings.AUTH_MODE,
        storage_mode=settings.STORAGE_MODE,
        catalogue_provider=settings.CATALOGUE_PROVIDER,
        database=database,
        embeddings=embeds,
        llm=llm,
        catalogue=catalogue,
    )


@router.get(
    "/health/keepalive",
    response_model=KeepaliveResponse,
    summary="Cheap ping that keeps a paused-on-idle project awake",
)
async def keepalive(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> KeepaliveResponse:
    started = time.perf_counter()
    await session.execute(text("select 1"))
    elapsed = int((time.perf_counter() - started) * 1000)
    return KeepaliveResponse(
        ok=True,
        database_roundtrip_ms=elapsed,
        note=(
            "Supabase pauses a free project after seven days without API "
            "requests. Schedule scripts/keepalive.py against this endpoint."
        ),
    )
