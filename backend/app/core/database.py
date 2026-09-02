"""Async SQLAlchemy engine and session dependency.

Pool configuration is derived from the DB URL, not hand-set, so switching
between local Docker, Supavisor session mode and Supavisor transaction mode is
a single environment change (§3 critical fact 5).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


def _engine_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {"echo": settings.DB_ECHO, "future": True}
    if settings.is_transaction_pooler:
        # Supavisor transaction mode multiplexes server connections, so a
        # prepared statement created on one is not visible on the next.
        log.info("DB: Supavisor transaction mode detected (:6543) — NullPool, no stmt cache")
        kwargs["poolclass"] = NullPool
        kwargs["connect_args"] = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        }
    else:
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 5
        kwargs["pool_pre_ping"] = True
        kwargs["pool_recycle"] = 1800
    return kwargs


engine: AsyncEngine = create_async_engine(settings.DB_URL, **_engine_kwargs())

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a session that always closes."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    await engine.dispose()
