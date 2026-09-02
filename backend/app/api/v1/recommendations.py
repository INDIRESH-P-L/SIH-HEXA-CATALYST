"""M5 · recommendation endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.errors import ConflictError, NotFoundError
from app.core.security import CurrentUserDep
from app.models.ai import ActivityLog
from app.models.course import Recommendation
from app.schemas.catalogue import CourseRead
from app.schemas.recommendation import (
    GenerateRequest,
    RecommendationBatch,
    RecommendationContext,
    PathwayStepRead,
    RecommendationRead,
    ScoreBreakdown,
)
from app.services import m5_recommender as recommender

router = APIRouter(prefix="/recommendations", tags=["M5 · recommendations"])


def _breakdown(raw: dict) -> ScoreBreakdown:
    """Rebuild the score breakdown from what was stored at generation time.

    Everything here was persisted when the batch was produced, so the interface
    shows the terms that actually decided the order rather than a recomputation
    that might drift from it.
    """
    sequence = raw.get("sequence")
    return ScoreBreakdown(
        gap_priority=float(raw.get("gap_priority", 0.0)),
        semantic_similarity=float(raw.get("semantic_similarity", 0.0)),
        level_fit=float(raw.get("level_fit", 0.0)),
        prerequisites_met=float(raw.get("prerequisites_met", 0.0)),
        effort_fit=float(raw.get("effort_fit", 0.0)),
        department_priority=float(raw.get("department_priority", 0.0)),
        recency_language=float(raw.get("recency_language", 0.0)),
        weights=dict(raw.get("weights", recommender.WEIGHTS)),
        final_score=float(raw.get("final_score", 0.0)),
        fusion_score=raw.get("fusion_score"),
        retrievers=raw.get("retrievers"),
        fusion=raw.get("fusion"),
        sequence=PathwayStepRead(**sequence) if sequence else None,
        gap_derivation=raw.get("gap_derivation"),
    )


def _to_read(row: Recommendation) -> RecommendationRead:
    raw = dict(row.breakdown or {})
    return RecommendationRead(
        id=row.id,
        batch_id=row.batch_id,
        rank=row.rank,
        score=float(row.score),
        course=CourseRead.model_validate(row.course),
        competency_id=row.competency_id,
        competency_code=raw.get("competency_code"),
        competency_name=raw.get("competency_name"),
        current_level=raw.get("current_level"),
        required_level=raw.get("required_level"),
        gap_band=raw.get("gap_band"),
        explanation=row.explanation,
        explanation_source=raw.get("explanation_source", "template"),
        breakdown=_breakdown(raw),
        created_at=row.created_at,
    )


@router.post(
    "/generate",
    response_model=RecommendationBatch,
    summary="Generate a fresh ranked batch",
)
async def generate(
    payload: GenerateRequest,
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RecommendationBatch:
    """Retrieve semantically, rank deterministically, explain with the model.

    Ranking never depends on the language model. If it is unavailable, every
    explanation falls back to a template and the ordering is unchanged.
    """
    if user.profile.job_role_id is None:
        raise ConflictError(
            "This officer has no job role assigned, so there are no requirements "
            "to recommend against."
        )

    batch_id, results = await recommender.generate(
        session,
        profile=user.profile,
        limit=payload.limit,
        max_per_competency=payload.max_per_competency,
        monthly_hours=payload.monthly_hours,
        explain_with_llm=payload.explain,
    )

    session.add(
        ActivityLog(
            user_id=user.id,
            action="recommendation.generate",
            entity="recommendations",
            entity_id=batch_id,
            extra={
                "count": len(results),
                "ai_explanations": sum(
                    1 for r in results if r.explanation_source == "ai"
                ),
            },
        )
    )
    await session.commit()

    rows = (
        await session.execute(
            select(Recommendation)
            .where(Recommendation.batch_id == batch_id)
            .order_by(Recommendation.rank)
        )
    ).scalars().all()

    return RecommendationBatch(
        batch_id=batch_id,
        generated_at=datetime.now(tz=timezone.utc),
        count=len(rows),
        ai_explanations=sum(1 for r in results if r.explanation_source == "ai"),
        llm_available=settings.llm_configured,
        recommendations=[_to_read(r) for r in rows],
    )


@router.get(
    "/me", response_model=RecommendationBatch, summary="Your latest ranked batch"
)
async def my_recommendations(
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
    batch: Annotated[
        str, Query(description="'latest' or a batch id.")
    ] = "latest",
) -> RecommendationBatch:
    if batch == "latest":
        batch_id = await session.scalar(
            select(Recommendation.batch_id)
            .where(Recommendation.user_id == user.id)
            .order_by(desc(Recommendation.created_at))
            .limit(1)
        )
        if batch_id is None:
            return RecommendationBatch(
                batch_id=uuid.UUID(int=0),
                generated_at=datetime.now(tz=timezone.utc),
                count=0,
                ai_explanations=0,
                llm_available=settings.llm_configured,
                recommendations=[],
            )
    else:
        try:
            batch_id = uuid.UUID(batch)
        except ValueError as exc:
            raise NotFoundError("Not a valid batch id.") from exc

    rows = (
        await session.execute(
            select(Recommendation)
            .where(Recommendation.user_id == user.id)
            .where(Recommendation.batch_id == batch_id)
            .order_by(Recommendation.rank)
        )
    ).scalars().all()

    reads = [_to_read(r) for r in rows]
    return RecommendationBatch(
        batch_id=batch_id,
        generated_at=rows[0].created_at if rows else datetime.now(tz=timezone.utc),
        count=len(reads),
        ai_explanations=sum(1 for r in reads if r.explanation_source == "ai"),
        llm_available=settings.llm_configured,
        recommendations=reads,
    )


@router.get(
    "/{recommendation_id}/breakdown",
    response_model=RecommendationContext,
    summary="Score terms and the exact anonymised context sent to the model",
)
async def breakdown(
    recommendation_id: uuid.UUID,
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RecommendationContext:
    """Show the arithmetic and the payload.

    The ``ai_context_sent`` field is the complete JSON that went to the model.
    It is stored at generation time rather than reconstructed, so what is shown
    is what was actually sent.
    """
    row = await session.get(Recommendation, recommendation_id)
    if row is None or row.user_id != user.id:
        raise NotFoundError("No such recommendation.")

    raw = dict(row.breakdown or {})
    return RecommendationContext(
        recommendation_id=row.id,
        rank=row.rank,
        score=float(row.score),
        breakdown=_breakdown(raw),
        ai_context_sent=dict(raw.get("ai_context_sent", {})),
        explanation=row.explanation,
        explanation_source=raw.get("explanation_source", "template"),
        model=raw.get("model"),
    )
