"""M3 · assessment endpoints — the closed loop.

``POST /assessments/{id}/submit`` is the endpoint the whole demonstration is
built around. It scores, updates the competency level, recomputes the gap and
regenerates recommendations, then returns the complete before-and-after picture
in one payload.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUserDep
from app.models.ai import ActivityLog
from app.models.assessment import AssessmentQuestion
from app.schemas.assessment import (
    AnswerRequest,
    AnswerResponse,
    AssessmentHistoryItem,
    AssessmentRead,
    CompetencyRef,
    CreateAssessmentRequest,
    GapSnapshot,
    NewRecommendationRef,
    ScoringBreakdown,
    SubmitResponse,
)
from app.schemas.question import QuizQuestion
from app.services import m3_assessment as service

router = APIRouter(prefix="/assessments", tags=["M3 · assessments"])


@router.post("", response_model=AssessmentRead, summary="Start an assessment")
async def create_assessment(
    payload: CreateAssessmentRequest,
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AssessmentRead:
    assessment = await service.create_assessment(
        session,
        user_id=user.id,
        competency_id=payload.competency_id,
        material_id=payload.material_id,
        count=payload.count,
        mode=payload.mode,
    )
    session.add(
        ActivityLog(
            user_id=user.id,
            action="assessment.start",
            entity="assessments",
            entity_id=assessment.id,
            extra={"total_questions": assessment.total_questions},
        )
    )
    await session.commit()
    return await _read(session, assessment.id, user.id)


async def _read(
    session: AsyncSession, assessment_id: uuid.UUID, user_id: uuid.UUID
) -> AssessmentRead:
    assessment = await service.load_assessment(session, assessment_id, user_id)
    items = await service.load_items(session, assessment_id)
    competency = assessment.competency

    answered = sum(1 for row, _q in items if row.selected_index is not None)
    return AssessmentRead(
        id=assessment.id,
        status=assessment.status,  # type: ignore[arg-type]
        competency_id=assessment.competency_id,
        competency_code=competency.code if competency else None,
        competency_name=competency.name if competency else None,
        material_id=assessment.material_id,
        total_questions=assessment.total_questions,
        answered_count=answered,
        started_at=assessment.started_at,
        questions=[
            # correct_index and explanation are omitted on purpose: the answer
            # key is never sent to the client while the assessment is open.
            QuizQuestion(
                id=question.id,
                position=row.position,
                question_text=question.question_text,
                options=list(question.options or []),
                difficulty=question.difficulty,  # type: ignore[arg-type]
                topic=question.topic,
                source_page=question.source_page,
                selected_index=row.selected_index,
            )
            for row, question in items
        ],
    )


@router.get(
    "/me",
    response_model=list[AssessmentHistoryItem],
    summary="Your assessment history",
)
async def my_assessments(
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[AssessmentHistoryItem]:
    rows = await service.history(session, user.id)
    return [
        AssessmentHistoryItem(
            id=a.id,
            status=a.status,  # type: ignore[arg-type]
            competency_code=c.code if c else None,
            competency_name=c.name if c else None,
            total_questions=a.total_questions,
            correct_count=a.correct_count,
            score=float(a.score) if a.score is not None else None,
            level_before=a.level_before,
            level_after=a.level_after,
            started_at=a.started_at,
            submitted_at=a.submitted_at,
        )
        for a, c in rows
    ]


@router.get(
    "/{assessment_id}",
    response_model=AssessmentRead,
    summary="The quiz, without the answer key",
)
async def get_assessment(
    assessment_id: uuid.UUID,
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AssessmentRead:
    return await _read(session, assessment_id, user.id)


@router.post(
    "/{assessment_id}/answer",
    response_model=AnswerResponse,
    summary="Record an answer",
)
async def answer(
    assessment_id: uuid.UUID,
    payload: AnswerRequest,
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AnswerResponse:
    assessment = await service.load_assessment(session, assessment_id, user.id)
    answered = await service.record_answer(
        session,
        assessment=assessment,
        question_id=payload.question_id,
        selected_index=payload.selected_index,
    )
    await session.commit()
    return AnswerResponse(
        assessment_id=assessment_id,
        question_id=payload.question_id,
        selected_index=payload.selected_index,
        answered_count=answered,
        total_questions=assessment.total_questions,
    )


@router.post(
    "/{assessment_id}/submit",
    response_model=SubmitResponse,
    summary="Score, update the competency, recompute the gap, re-recommend",
)
async def submit(
    assessment_id: uuid.UUID,
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SubmitResponse:
    """The closed loop, in one call.

    Steps 1-6 (score, level before, level after, evidence row, gap recompute,
    new recommendation batch) commit together. Step 7, the written feedback,
    runs afterwards and degrades to a template if the model is unavailable —
    it can never fail the request.
    """
    assessment = await service.load_assessment(session, assessment_id, user.id)

    result = await service.submit(session, assessment=assessment, profile=user.profile)

    session.add(
        ActivityLog(
            user_id=user.id,
            action="assessment.submit",
            entity="assessments",
            entity_id=assessment_id,
            extra={
                "weighted_score": result.score,
                "raw_score": result.raw_score,
                "mode": result.mode,
                "level_before": result.level_before,
                "level_after": result.level_after,
                "revisit": result.revisit,
                "batch_id": str(result.batch_id),
            },
        )
    )
    # Steps 1-6 land here, together.
    await session.commit()

    # Step 7: best-effort, outside the loop's transaction.
    feedback, feedback_source = await service.add_feedback(
        session, result=result, user_id=user.id
    )
    await session.commit()

    return SubmitResponse(
        assessment_id=assessment_id,
        score=result.score,
        raw_score=result.raw_score,
        breakdown=ScoringBreakdown(**result.breakdown.as_dict()),
        mode=result.mode,
        confidence=result.confidence,
        correct_count=result.correct_count,
        attempted=result.attempted,
        total_questions=result.total_questions,
        competency=CompetencyRef(
            id=result.competency.id,
            code=result.competency.code,
            name=result.competency.name,
        ),
        level_before=result.level_before,
        level_after=result.level_after,
        level_changed=result.level_after != result.level_before,
        frac_before=result.frac_before,
        frac_after=result.frac_after,
        gap_before=GapSnapshot(
            gap=result.gap_before, band=result.band_before, frac=result.frac_before
        ),
        gap_after=GapSnapshot(
            gap=result.gap_after, band=result.band_after, frac=result.frac_after
        ),
        priority_before=result.priority_before,
        priority_after=result.priority_after,
        weak_topics=result.weak_topics,
        strong_topics=result.strong_topics,
        revisit=result.revisit,
        ai_feedback=feedback,
        feedback_source=feedback_source,
        new_recommendations=[
            NewRecommendationRef(
                rank=r.rank,
                course_id=r.candidate.course_id,
                title=r.candidate.offering.title,
                provider=r.candidate.offering.source,
                source=r.candidate.offering.source,
                proficiency_level=r.candidate.offering.proficiency_level,
                duration_hours=r.candidate.offering.duration_hours,
                explanation=r.explanation,
                explanation_source=r.explanation_source,
            )
            for r in result.recommendations
        ],
        evidence_id=result.evidence_id,
    )
