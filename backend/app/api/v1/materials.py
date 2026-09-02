"""M8 · learning material upload and question generation (trainer)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.errors import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.core.security import CurrentUser, require_role
from app.models.ai import ActivityLog
from app.models.competency import Competency
from app.models.material import LearningMaterial, MaterialChunk
from app.models.question import Question
from app.schemas.material import ChunkRead, GenerateQuestionsRequest, MaterialRead
from app.schemas.question import GenerationSummary, QuestionRead, ValidationReport
from app.services.m8_generator import pipeline
from app.services.storage import get_storage_provider

log = get_logger(__name__)
router = APIRouter(prefix="/materials", tags=["M8 · materials & generation"])

TrainerDep = Annotated[CurrentUser, Depends(require_role("trainer"))]


async def _to_read(session: AsyncSession, material: LearningMaterial) -> MaterialRead:
    counts = await pipeline.material_counts(session, material.id)
    competency = (
        await session.get(Competency, material.competency_id)
        if material.competency_id
        else None
    )
    return MaterialRead(
        id=material.id,
        title=material.title,
        filename=material.filename,
        file_type=material.file_type,
        competency_id=material.competency_id,
        competency_code=competency.code if competency else None,
        competency_name=competency.name if competency else None,
        status=material.status,  # type: ignore[arg-type]
        page_count=material.page_count,
        char_count=material.char_count,
        chunk_count=counts["chunk_count"],
        question_count=counts["question_count"],
        approved_count=counts["approved_count"],
        corpus_approved=material.corpus_approved,
        error=material.error,
        created_at=material.created_at,
    )


def _question_read(row: Question) -> QuestionRead:
    return QuestionRead(
        id=row.id,
        material_id=row.material_id,
        competency_id=row.competency_id,
        question_text=row.question_text,
        options=list(row.options or []),
        correct_index=row.correct_index,
        explanation=row.explanation,
        difficulty=row.difficulty,  # type: ignore[arg-type]
        topic=row.topic,
        status=row.status,  # type: ignore[arg-type]
        validation=(
            ValidationReport.model_validate(row.validation) if row.validation else None
        ),
        source_page=row.source_page,
        created_at=row.created_at,
    )


@router.post("", response_model=MaterialRead, summary="Upload training material")
async def upload_material(
    actor: TrainerDep,
    session: Annotated[AsyncSession, Depends(get_session)],
    file: Annotated[UploadFile, File(description="PDF, DOCX or PPTX, max 10 MB.")],
    title: Annotated[str, Form()],
    competency_id: Annotated[uuid.UUID | None, Form()] = None,
) -> MaterialRead:
    """Store the file, extract, clean, chunk and embed it.

    The client filename is recorded for display but never used to build the
    storage key; the stored object is named from a server-generated UUID.
    """
    data = await file.read()
    extension = pipeline.extract.validate_upload(
        file.filename or "upload", file.content_type, len(data), settings.upload_limit_bytes
    )

    if competency_id is not None and await session.get(Competency, competency_id) is None:
        raise NotFoundError("No such competency.")

    storage = get_storage_provider()
    stored = await storage.put(
        user_id=actor.id,
        data=data,
        extension=extension,
        content_type=file.content_type or "application/octet-stream",
    )

    material = LearningMaterial(
        uploaded_by=actor.id,
        title=title.strip(),
        filename=(file.filename or f"upload.{extension}")[:255],
        storage_path=stored.path,
        file_type=extension,
        competency_id=competency_id,
        status="UPLOADED",
        corpus_approved=True,
    )
    session.add(material)
    await session.flush()

    try:
        await pipeline.extract_and_chunk(session, material, data)
    except Exception:
        # The material row is kept with status FAILED and a stored reason, so
        # the trainer sees why rather than seeing nothing.
        await session.commit()
        refreshed = await session.get(LearningMaterial, material.id)
        assert refreshed is not None
        return await _to_read(session, refreshed)

    session.add(
        ActivityLog(
            user_id=actor.id,
            action="material.upload",
            entity="learning_materials",
            entity_id=material.id,
            extra={"file_type": extension, "bytes": len(data)},
        )
    )
    await session.commit()
    return await _to_read(session, material)


@router.get("", response_model=list[MaterialRead], summary="Your uploaded materials")
async def list_materials(
    actor: TrainerDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[MaterialRead]:
    stmt = select(LearningMaterial).order_by(LearningMaterial.created_at.desc())
    if not actor.is_admin:
        stmt = stmt.where(LearningMaterial.uploaded_by == actor.id)
    rows = (await session.execute(stmt)).scalars().all()
    return [await _to_read(session, m) for m in rows]


@router.get("/{material_id}", response_model=MaterialRead, summary="One material")
async def get_material(
    material_id: uuid.UUID,
    actor: TrainerDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MaterialRead:
    material = await pipeline.get_material(session, material_id)
    if material.uploaded_by != actor.id and not actor.is_admin:
        raise ForbiddenError("That material was uploaded by another trainer.")
    return await _to_read(session, material)


@router.get(
    "/{material_id}/chunks",
    response_model=list[ChunkRead],
    summary="The extracted chunks, for inspection",
)
async def list_chunks(
    material_id: uuid.UUID,
    actor: TrainerDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ChunkRead]:
    material = await pipeline.get_material(session, material_id)
    if material.uploaded_by != actor.id and not actor.is_admin:
        raise ForbiddenError("That material was uploaded by another trainer.")

    rows = (
        await session.execute(
            select(MaterialChunk)
            .where(MaterialChunk.material_id == material_id)
            .order_by(MaterialChunk.chunk_index)
        )
    ).scalars().all()
    return [
        ChunkRead(
            id=c.id,
            chunk_index=c.chunk_index,
            page_no=c.page_no,
            content=c.content,
            char_count=len(c.content),
        )
        for c in rows
    ]


@router.post(
    "/{material_id}/generate",
    response_model=GenerationSummary,
    summary="Generate questions and run the validation gate",
)
async def generate_questions(
    material_id: uuid.UUID,
    payload: GenerateQuestionsRequest,
    actor: TrainerDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GenerationSummary:
    """Generate with the model, then filter with rules.

    The response is the validation report: how many were generated, how many
    survived, and which check rejected each of the rest.
    """
    material = await pipeline.get_material(session, material_id)
    if material.uploaded_by != actor.id and not actor.is_admin:
        raise ForbiddenError("That material was uploaded by another trainer.")

    outcome = await pipeline.generate_questions(
        session,
        material=material,
        num_questions=payload.num_questions,
        difficulty_mix=payload.difficulty_mix,
        auto_approve_passing=payload.auto_approve_passing,
        user_id=actor.id,
    )

    session.add(
        ActivityLog(
            user_id=actor.id,
            action="material.generate",
            entity="questions",
            entity_id=material.id,
            extra={
                "requested": outcome.requested,
                "generated": outcome.generated,
                "passed": outcome.passed,
                "rejected": outcome.rejected,
            },
        )
    )
    await session.commit()

    accepted = (
        await session.execute(select(Question).where(Question.id.in_(outcome.accepted_ids)))
    ).scalars().all() if outcome.accepted_ids else []
    rejected = (
        await session.execute(select(Question).where(Question.id.in_(outcome.rejected_ids)))
    ).scalars().all() if outcome.rejected_ids else []

    return GenerationSummary(
        material_id=material.id,
        requested=outcome.requested,
        generated=outcome.generated,
        passed=outcome.passed,
        rejected=outcome.rejected,
        retried=outcome.retried,
        chunks_used=outcome.chunks_used,
        llm_available=outcome.llm_available,
        model=outcome.model,
        rejection_reasons=dict(outcome.rejection_reasons),
        check_pass_counts=dict(outcome.check_pass_counts),
        questions=[_question_read(q) for q in accepted],
        rejected_questions=[_question_read(q) for q in rejected],
        note=outcome.note,
    )


@router.get(
    "/{material_id}/questions",
    response_model=list[QuestionRead],
    summary="Questions generated from this material, with validation reports",
)
async def list_questions(
    material_id: uuid.UUID,
    actor: TrainerDep,
    session: Annotated[AsyncSession, Depends(get_session)],
    status: str | None = None,
) -> list[QuestionRead]:
    material = await pipeline.get_material(session, material_id)
    if material.uploaded_by != actor.id and not actor.is_admin:
        raise ForbiddenError("That material was uploaded by another trainer.")

    stmt = select(Question).where(Question.material_id == material_id)
    if status:
        stmt = stmt.where(Question.status == status.upper())
    stmt = stmt.order_by(Question.created_at)

    rows = (await session.execute(stmt)).scalars().all()
    return [_question_read(q) for q in rows]


@router.post(
    "/{material_id}/toggle-corpus",
    response_model=MaterialRead,
    summary="Toggle approval for assistant corpus",
)
async def toggle_corpus(
    material_id: uuid.UUID,
    actor: TrainerDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MaterialRead:
    material = await pipeline.get_material(session, material_id)
    if material.uploaded_by != actor.id and not actor.is_admin:
        raise ForbiddenError("That material was uploaded by another trainer.")
    material.corpus_approved = not material.corpus_approved
    await session.commit()
    return await _to_read(session, material)
