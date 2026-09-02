"""M8 · the end-to-end generation pipeline.

    upload -> extract -> clean -> chunk -> embed -> select chunks
           -> generate (Groq, strict JSON) -> validate (deterministic)
           -> one retry for rejects -> store as DRAFT

Only the generation step involves a model. Selection is cosine similarity,
validation is rules, and the counts in the report are counts.
"""

from __future__ import annotations

import uuid
from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import embeddings
from app.core.config import settings
from app.core.errors import ConflictError, NotFoundError, ValidationFailedError
from app.core.logging import get_logger
from app.models.competency import Competency
from app.models.material import LearningMaterial, MaterialChunk
from app.models.question import Question
from app.services.m8_generator import clean, extract, generate, validate
from app.services.m8_generator.chunk import Chunk, chunk_pages

log = get_logger(__name__)


@dataclass
class GenerationOutcome:
    """Everything the trainer's validation report needs."""

    material_id: uuid.UUID
    requested: int
    generated: int = 0
    passed: int = 0
    rejected: int = 0
    retried: int = 0
    chunks_used: int = 0
    llm_available: bool = False
    model: str | None = None
    rejection_reasons: Counter[str] = field(default_factory=Counter)
    check_pass_counts: Counter[str] = field(default_factory=Counter)
    accepted_ids: list[uuid.UUID] = field(default_factory=list)
    rejected_ids: list[uuid.UUID] = field(default_factory=list)
    note: str | None = None


async def extract_and_chunk(
    session: AsyncSession, material: LearningMaterial, data: bytes
) -> list[Chunk]:
    """Extract, clean, chunk, embed and persist.

    Failures are written to ``learning_materials.error`` and the status is set
    to FAILED, so the interface can explain what went wrong instead of showing
    an empty question list.
    """
    try:
        extraction = extract.extract(data, material.file_type)
    except ValidationFailedError as exc:
        material.status = "FAILED"
        material.error = exc.message
        await session.flush()
        raise

    material.page_count = extraction.page_count
    material.char_count = extraction.char_count
    material.status = "EXTRACTED"
    await session.flush()

    cleaned = clean.clean_extraction(extraction)
    chunks = chunk_pages([(p.page_no, p.text) for p in cleaned.pages])

    if not chunks:
        material.status = "FAILED"
        material.error = "No usable text remained after cleaning."
        await session.flush()
        raise ValidationFailedError(material.error)

    # Replace any previous chunks so re-processing a document is idempotent.
    existing = (
        await session.execute(
            select(MaterialChunk).where(MaterialChunk.material_id == material.id)
        )
    ).scalars().all()
    for row in existing:
        await session.delete(row)
    await session.flush()

    vectors = embeddings.embed_many([c.content for c in chunks])
    for chunk, vector in zip(chunks, vectors):
        session.add(
            MaterialChunk(
                material_id=material.id,
                chunk_index=chunk.index,
                content=chunk.content,
                page_no=chunk.page_no,
                embedding=vector,
            )
        )

    material.status = "CHUNKED"
    await session.flush()
    log.info(
        "material %s: %d pages, %d chars, %d chunks",
        material.id,
        extraction.page_count,
        extraction.char_count,
        len(chunks),
    )
    return chunks


async def select_chunks(
    session: AsyncSession,
    material: LearningMaterial,
    competency: Competency | None,
    limit: int,
) -> list[Chunk]:
    """Pick the chunks most relevant to the target competency.

    With a competency, ranking is cosine distance against its embedding. Without
    one, document order is used — it is at least the author's own ordering.
    """
    if competency is not None and competency.embedding is not None:
        vector = embeddings.embed_one(f"{competency.name}. {competency.description}")
        rows = (
            await session.execute(
                select(MaterialChunk)
                .where(MaterialChunk.material_id == material.id)
                .where(MaterialChunk.embedding.isnot(None))
                .order_by(MaterialChunk.embedding.cosine_distance(vector))
                .limit(limit)
            )
        ).scalars().all()
        if rows:
            # Restore document order among the selected chunks so generated
            # items follow the handout rather than the ranking.
            rows = sorted(rows, key=lambda r: r.chunk_index)
            return [
                Chunk(index=r.chunk_index, content=r.content, page_no=r.page_no)
                for r in rows
            ]

    rows = (
        await session.execute(
            select(MaterialChunk)
            .where(MaterialChunk.material_id == material.id)
            .order_by(MaterialChunk.chunk_index)
            .limit(limit)
        )
    ).scalars().all()
    return [
        Chunk(index=r.chunk_index, content=r.content, page_no=r.page_no) for r in rows
    ]


async def _existing_bank_embeddings(
    session: AsyncSession, competency_id: uuid.UUID | None
) -> list[list[float]]:
    """Embeddings of items already in the bank for this competency."""
    if competency_id is None:
        return []
    rows = (
        await session.execute(
            select(Question.embedding)
            .where(Question.competency_id == competency_id)
            .where(Question.embedding.isnot(None))
            .where(Question.status != "REJECTED")
        )
    ).scalars().all()
    return [list(v) for v in rows if v is not None]


async def _chunk_id_for(
    session: AsyncSession, material_id: uuid.UUID, chunk_index: int
) -> uuid.UUID | None:
    return await session.scalar(
        select(MaterialChunk.id)
        .where(MaterialChunk.material_id == material_id)
        .where(MaterialChunk.chunk_index == chunk_index)
    )


async def generate_questions(
    session: AsyncSession,
    *,
    material: LearningMaterial,
    num_questions: int,
    difficulty_mix: str = "balanced",
    auto_approve_passing: bool = False,
    user_id: uuid.UUID | None = None,
) -> GenerationOutcome:
    """Generate, validate and store items for one material."""
    competency = (
        await session.get(Competency, material.competency_id)
        if material.competency_id
        else None
    )
    competency_name = competency.name if competency else "the uploaded material"

    chunks_needed = max(1, -(-num_questions // generate.QUESTIONS_PER_CHUNK))
    chunks = await select_chunks(session, material, competency, chunks_needed)
    if not chunks:
        raise ConflictError(
            "This material has no chunks yet. Re-upload it or re-run extraction."
        )

    outcome = GenerationOutcome(
        material_id=material.id,
        requested=num_questions,
        chunks_used=len(chunks),
        llm_available=settings.llm_configured,
        model=settings.MODEL_MCQ if settings.llm_configured else None,
    )

    # Near-duplicate comparison runs against the existing bank AND everything
    # accepted so far in this run, so a batch cannot duplicate within itself.
    comparison_pool = await _existing_bank_embeddings(session, material.competency_id)

    for chunk in chunks:
        if outcome.passed >= num_questions:
            break

        items = await generate.generate_for_chunk(
            session,
            chunk=chunk,
            competency_name=competency_name,
            user_id=user_id,
            num_questions=generate.QUESTIONS_PER_CHUNK,
            difficulty_mix=difficulty_mix,
        )
        outcome.generated += len(items)
        if not items:
            continue

        retry_reasons: list[str] = []

        for item in items:
            vector = embeddings.embed_one(item.embedding_text)
            result = validate.validate_item(
                item.as_dict(),
                source_chunk=chunk.content,
                embedding=vector,
                existing_embeddings=comparison_pool,
            )

            for name, check in result.checks.items():
                if check.passed:
                    outcome.check_pass_counts[name] += 1
                else:
                    outcome.rejection_reasons[name] += 1

            chunk_id = await _chunk_id_for(session, material.id, chunk.index)
            question = Question(
                material_id=material.id,
                chunk_id=chunk_id,
                competency_id=material.competency_id,
                question_text=item.question_text,
                options=item.options,
                correct_index=max(0, min(3, item.correct_index)),
                explanation=item.explanation or "No explanation was produced.",
                difficulty=(
                    item.difficulty if item.difficulty in validate.VALID_DIFFICULTIES else "medium"
                ),
                topic=item.topic or None,
                status=(
                    ("APPROVED" if auto_approve_passing else "DRAFT")
                    if result.passed
                    else "REJECTED"
                ),
                validation=result.as_json(),
                source_page=chunk.page_no,
                embedding=vector,
            )
            session.add(question)
            await session.flush()

            if result.passed:
                outcome.passed += 1
                outcome.accepted_ids.append(question.id)
                comparison_pool.append(vector)
            else:
                outcome.rejected += 1
                outcome.rejected_ids.append(question.id)
                retry_reasons.append(result.failure_reason())

        # Exactly one retry per chunk, carrying the failure reasons forward.
        # Anything still failing is dropped rather than retried again.
        if retry_reasons and outcome.passed < num_questions:
            outcome.retried += 1
            retry_items = await generate.generate_for_chunk(
                session,
                chunk=chunk,
                competency_name=competency_name,
                user_id=user_id,
                num_questions=min(len(retry_reasons), generate.QUESTIONS_PER_CHUNK),
                difficulty_mix=difficulty_mix,
                retry_reason=retry_reasons[0],
            )
            outcome.generated += len(retry_items)

            for item in retry_items:
                vector = embeddings.embed_one(item.embedding_text)
                result = validate.validate_item(
                    item.as_dict(),
                    source_chunk=chunk.content,
                    embedding=vector,
                    existing_embeddings=comparison_pool,
                )
                for name, check in result.checks.items():
                    if check.passed:
                        outcome.check_pass_counts[name] += 1
                    else:
                        outcome.rejection_reasons[name] += 1

                if not result.passed:
                    outcome.rejected += 1
                    continue

                chunk_id = await _chunk_id_for(session, material.id, chunk.index)
                question = Question(
                    material_id=material.id,
                    chunk_id=chunk_id,
                    competency_id=material.competency_id,
                    question_text=item.question_text,
                    options=item.options,
                    correct_index=max(0, min(3, item.correct_index)),
                    explanation=item.explanation,
                    difficulty=(
                        item.difficulty
                        if item.difficulty in validate.VALID_DIFFICULTIES
                        else "medium"
                    ),
                    topic=item.topic or None,
                    status="APPROVED" if auto_approve_passing else "DRAFT",
                    validation=result.as_json(),
                    source_page=chunk.page_no,
                    embedding=vector,
                )
                session.add(question)
                await session.flush()
                outcome.passed += 1
                outcome.accepted_ids.append(question.id)
                comparison_pool.append(vector)

    material.status = "GENERATED" if outcome.passed else material.status
    if not outcome.llm_available:
        outcome.note = (
            "No GROQ_API_KEY is configured, so no items could be generated from "
            "this document. The seeded question bank is still available for the "
            "assessment loop."
        )
    elif outcome.generated == 0:
        outcome.note = (
            "The language model returned no items. This is usually a rate limit; "
            "try again in a minute."
        )
    await session.flush()

    log.info(
        "material %s: %d generated, %d passed, %d rejected across %d chunks",
        material.id,
        outcome.generated,
        outcome.passed,
        outcome.rejected,
        outcome.chunks_used,
    )
    return outcome


async def material_counts(
    session: AsyncSession, material_id: uuid.UUID
) -> dict[str, int]:
    chunk_count = await session.scalar(
        select(func.count())
        .select_from(MaterialChunk)
        .where(MaterialChunk.material_id == material_id)
    )
    question_count = await session.scalar(
        select(func.count()).select_from(Question).where(Question.material_id == material_id)
    )
    approved = await session.scalar(
        select(func.count())
        .select_from(Question)
        .where(Question.material_id == material_id)
        .where(Question.status == "APPROVED")
    )
    return {
        "chunk_count": int(chunk_count or 0),
        "question_count": int(question_count or 0),
        "approved_count": int(approved or 0),
    }


async def get_material(
    session: AsyncSession, material_id: uuid.UUID
) -> LearningMaterial:
    material = await session.get(LearningMaterial, material_id)
    if material is None:
        raise NotFoundError("No such material.")
    return material
