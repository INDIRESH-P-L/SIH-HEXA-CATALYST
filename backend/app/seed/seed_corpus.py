"""Ingest the sample handouts into the assistant's approved corpus.

The assistant answers from material a trainer has approved, not from whatever
happens to have been uploaded. Seeding runs the real pipeline — extract, clean,
chunk, embed — and then marks the material approved, so what the assistant
retrieves at demonstration time is exactly what the upload path would have
produced.

Only the SQL handout is approved by default. ``Sampling_Methods_Primer.pdf`` is
deliberately left out: it is the document held back for a live cold ingestion,
and having it already in the corpus would spoil that.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.competency import Competency
from app.models.material import LearningMaterial, MaterialChunk
from app.models.user import Profile
from app.services.m8_generator import pipeline

log = get_logger(__name__)

ASSETS = Path(__file__).resolve().parent / "assets"

#: (filename, title, competency code). Approved into the corpus on seed.
CORPUS_DOCUMENTS: list[tuple[str, str, str]] = [
    (
        "SQL_Fundamentals_for_Statistical_Analysis.pdf",
        "SQL Fundamentals for Statistical Analysis",
        "SQL",
    ),
]


async def _trainer_id(session: AsyncSession) -> uuid.UUID | None:
    profile = await session.scalar(
        select(Profile).where(Profile.full_name == "Anand Desai")
    )
    return profile.id if profile else None


async def seed_corpus(session: AsyncSession) -> dict[str, int]:
    """Ingest and approve the seeded documents. Idempotent on title."""
    uploaded_by = await _trainer_id(session)
    materials = 0

    for filename, title, competency_code in CORPUS_DOCUMENTS:
        path = ASSETS / filename
        if not path.is_file():
            log.warning(
                "corpus document missing: %s — run scripts/make_sample_docs.py", filename
            )
            continue

        existing = await session.scalar(
            select(LearningMaterial).where(LearningMaterial.title == title)
        )
        if existing is not None:
            if not existing.corpus_approved:
                existing.corpus_approved = True
                await session.flush()
            materials += 1
            continue

        competency = await session.scalar(
            select(Competency).where(Competency.code == competency_code)
        )
        material = LearningMaterial(
            uploaded_by=uploaded_by,
            title=title,
            filename=filename,
            # Seeded documents live in the repository rather than object
            # storage; the path records where they came from.
            storage_path=f"seed/{filename}",
            file_type="pdf",
            competency_id=competency.id if competency else None,
            status="UPLOADED",
            corpus_approved=True,
        )
        session.add(material)
        await session.flush()

        # The real pipeline, so the corpus holds exactly what an upload would.
        await pipeline.extract_and_chunk(session, material, path.read_bytes())
        materials += 1
        log.info("ingested %s into the approved corpus", filename)

    chunks = await session.scalar(
        select(func.count())
        .select_from(MaterialChunk)
        .join(LearningMaterial, LearningMaterial.id == MaterialChunk.material_id)
        .where(LearningMaterial.corpus_approved.is_(True))
    )

    await session.flush()
    return {"materials": materials, "chunks": int(chunks or 0)}
