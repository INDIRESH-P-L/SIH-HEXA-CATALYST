"""Catalogue synchronisation: pull, normalise, embed, upsert.

The ``courses`` table is a local mirror of whatever the configured provider
serves. Keeping a mirror does three things: it makes semantic search possible
at all (the vectors have to live next to the query), it keeps recommendations
working when the catalogue service is unreachable, and it means a demo does not
depend on a second process staying up.

Embeddings are computed here, in-process, with FastEmbed. Nothing is sent to
Groq — Groq has no embeddings endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import embeddings
from app.core.logging import get_logger
from app.models.course import Course
from app.services.m6_catalogue.provider import CatalogueProvider, OfferingDTO

log = get_logger(__name__)


@dataclass(frozen=True)
class SyncResult:
    """What a sync run did."""

    fetched: int
    upserted: int
    embedded: int
    igot: int
    nssta: int
    provider: str
    is_mock: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "fetched": self.fetched,
            "upserted": self.upserted,
            "embedded": self.embedded,
            "igot": self.igot,
            "nssta": self.nssta,
            "provider": self.provider,
            "is_mock": self.is_mock,
        }


async def upsert_offerings(
    session: AsyncSession, offerings: list[OfferingDTO]
) -> tuple[int, int]:
    """Write offerings into the mirror, computing embeddings in one batch.

    Returns (upserted, embedded). Conflict target is (source, external_id),
    which is the catalogue's own natural key, so re-syncing updates in place
    rather than duplicating.
    """
    if not offerings:
        return 0, 0

    # One batch call: embedding 20 short documents individually would be
    # needlessly slow, and FastEmbed batches efficiently.
    vectors = embeddings.embed_many([o.embedding_text for o in offerings])

    for offering, vector in zip(offerings, vectors):
        values = {
            "external_id": offering.external_id,
            "source": offering.source,
            "title": offering.title,
            "provider": offering.provider,
            "competency_code": offering.competency_code,
            "proficiency_level": offering.proficiency_level,
            "duration_hours": offering.duration_hours,
            "description": offering.description,
            "prerequisites": offering.prerequisites,
            "learning_format": offering.learning_format,
            "course_url": offering.course_url,
            "status": offering.status,
            "session_start": offering.session_start,
            "seats": offering.seats,
            "embedding": vector,
            "synced_at": func.now(),
        }
        stmt = (
            pg_insert(Course)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[Course.source, Course.external_id],
                set_={k: v for k, v in values.items() if k not in ("source", "external_id")},
            )
        )
        await session.execute(stmt)

    await session.flush()
    return len(offerings), len(vectors)


async def sync_catalogue(
    session: AsyncSession, provider: CatalogueProvider
) -> SyncResult:
    """Pull the whole catalogue from the provider and refresh the mirror."""
    offerings = await provider.list_courses()
    upserted, embedded = await upsert_offerings(session, offerings)

    info = provider.info()
    result = SyncResult(
        fetched=len(offerings),
        upserted=upserted,
        embedded=embedded,
        igot=sum(1 for o in offerings if o.source == "IGOT"),
        nssta=sum(1 for o in offerings if o.source == "NSSTA"),
        provider=info.provider,
        is_mock=info.is_mock,
    )
    log.info(
        "catalogue sync from %s provider: %d fetched (%d iGOT, %d NSSTA), %d embedded",
        result.provider,
        result.fetched,
        result.igot,
        result.nssta,
        result.embedded,
    )
    return result


async def mirror_stats(session: AsyncSession) -> dict[str, int]:
    """Counts used by /catalogue/provider-info and the health endpoint."""
    total = await session.scalar(select(func.count()).select_from(Course)) or 0
    embedded = (
        await session.scalar(
            select(func.count()).select_from(Course).where(Course.embedding.isnot(None))
        )
        or 0
    )
    return {"total": int(total), "embedded": int(embedded)}
