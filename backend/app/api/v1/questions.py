"""M8 · trainer review of generated questions."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import embeddings
from app.core.database import get_session
from app.core.errors import ForbiddenError, NotFoundError, ValidationFailedError
from app.core.security import CurrentUser, require_role
from app.models.ai import ActivityLog
from app.models.material import LearningMaterial
from app.models.question import Question
from app.schemas.question import QuestionRead, QuestionUpdate, ValidationReport

router = APIRouter(prefix="/questions", tags=["M8 · materials & generation"])

TrainerDep = Annotated[CurrentUser, Depends(require_role("trainer"))]


def _read(row: Question) -> QuestionRead:
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


@router.get("/{question_id}", response_model=QuestionRead, summary="One question")
async def get_question(
    question_id: uuid.UUID,
    actor: TrainerDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuestionRead:
    row = await session.get(Question, question_id)
    if row is None:
        raise NotFoundError("No such question.")
    return _read(row)


@router.patch(
    "/{question_id}",
    response_model=QuestionRead,
    summary="Approve, reject or edit a generated question",
)
async def update_question(
    question_id: uuid.UUID,
    payload: QuestionUpdate,
    actor: TrainerDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuestionRead:
    """Trainer review.

    Editing the stem or options recomputes the embedding, so near-duplicate
    detection keeps working against the edited text rather than the original.
    """
    row = await session.get(Question, question_id)
    if row is None:
        raise NotFoundError("No such question.")

    if row.material_id is not None and not actor.is_admin:
        material = await session.get(LearningMaterial, row.material_id)
        if material is not None and material.uploaded_by != actor.id:
            raise ForbiddenError("That question belongs to another trainer's material.")

    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        return _read(row)

    if "options" in changes:
        options = [str(o).strip() for o in changes["options"]]
        if len(options) != 4 or any(not o for o in options):
            raise ValidationFailedError("A question needs exactly four non-empty options.")
        changes["options"] = options

    for field, value in changes.items():
        setattr(row, field, value)

    if "question_text" in changes or "options" in changes:
        row.embedding = embeddings.embed_one(
            f"{row.question_text} {' '.join(row.options or [])}"
        )

    session.add(
        ActivityLog(
            user_id=actor.id,
            action="question.review",
            entity="questions",
            entity_id=row.id,
            extra={"fields": sorted(changes), "status": row.status},
        )
    )
    await session.commit()
    await session.refresh(row)
    return _read(row)
