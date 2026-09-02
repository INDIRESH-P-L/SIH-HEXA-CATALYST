"""FastAPI application entry point.

Run with::

    uvicorn app.main:app --reload
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.ai import embeddings
from app.api.v1.router import api_router
from app.api.v1.health import router as system_router
from app.core.config import settings
from app.core.database import SessionLocal, dispose_engine
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)


async def _keepalive_loop() -> None:
    """Ping the database on an interval so an idle project is not paused.

    Off by default. Enable with KEEPALIVE_ENABLED=true when the backend is
    left running against a Supabase free project.
    """
    interval = max(1, settings.KEEPALIVE_INTERVAL_H) * 3600
    while True:
        await asyncio.sleep(interval)
        try:
            async with SessionLocal() as session:
                await session.execute(text("select 1"))
            log.info("keepalive: database pinged")
        except Exception as exc:  # never let the loop die
            log.warning("keepalive ping failed: %s", exc)


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    log.info("%s starting (env=%s)", settings.APP_NAME, settings.APP_ENV)
    log.info(
        "seams: auth=%s storage=%s catalogue=%s | llm=%s",
        settings.AUTH_MODE,
        settings.STORAGE_MODE,
        settings.CATALOGUE_PROVIDER,
        "configured" if settings.llm_configured else "fallback-only (no GROQ_API_KEY)",
    )

    # Warm the embedding model so the first real request is not slow. Loading
    # happens off the event loop because it is CPU-bound ONNX initialisation.
    await asyncio.to_thread(embeddings.warm)
    log.info("embedding model warm")

    try:
        async with SessionLocal() as session:
            await session.execute(text("select 1"))
        log.info("database reachable")
    except Exception as exc:
        log.warning("database not reachable at startup: %s", exc)

    task: asyncio.Task[None] | None = None
    if settings.KEEPALIVE_ENABLED:
        task = asyncio.create_task(_keepalive_loop())
        log.info("keepalive enabled every %dh", settings.KEEPALIVE_INTERVAL_H)

    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await dispose_engine()
        log.info("shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description=(
        "Competency profiling, deterministic skill-gap analysis, semantic course "
        "recommendation and AI-generated assessments for officials in India's "
        "Official Statistical System.\n\n"
        "The course catalogue is served by a mock service conforming to a "
        "documented interface. Production deployment requires authorised API "
        "credentials from the Capacity Building Commission (iGOT) and NSSTA."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Explicit origin allowlist. Never "*" (§13.8).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

register_exception_handlers(app)

# /health and /health/keepalive sit at the root, outside the versioned prefix,
# so a monitor does not have to know the API version.
app.include_router(system_router)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "name": settings.APP_NAME,
        "docs": "/docs",
        "health": "/health",
        "api": settings.API_V1_PREFIX,
    }
