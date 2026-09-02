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


# ── Initial Competency Assessment endpoints ───────────────────────────────────
# These three endpoints orchestrate the new-user assessment flow that sits
# between onboarding (self-declaration) and course recommendation.


from pydantic import BaseModel  # noqa: E402  (local import for inline schemas)


class InitialTopicRead(BaseModel):
    """One competency that will be tested in the initial assessment."""
    competency_id: uuid.UUID
    competency_code: str
    competency_name: str
    cluster: str
    required_level: int
    question_count: int
    criticality: float


class InitialTopicsResponse(BaseModel):
    topics: list[InitialTopicRead]
    total_questions: int


class StartedAssessmentRef(BaseModel):
    competency_id: uuid.UUID
    competency_code: str
    competency_name: str
    assessment_id: uuid.UUID
    question_count: int


class InitialStartResponse(BaseModel):
    assessments: list[StartedAssessmentRef]
    total_questions: int


class InitialCompleteRequest(BaseModel):
    """List of assessment IDs that have been submitted by the frontend."""
    assessment_ids: list[uuid.UUID]


class CompetencyResult(BaseModel):
    competency_id: uuid.UUID
    competency_code: str
    competency_name: str
    score: float           # 0–100
    correct: int
    total: int
    level_before: int
    level_after: int
    level_label: str       # "Beginner" / "Basic" / "Intermediate" / "Advanced" / "Expert"
    required_level: int
    required_label: str
    gap: int               # required_level - level_after  (negative = above required)
    gap_band: str          # "critical" / "high" / "medium" / "none" / "above_required"


class InitialCompleteResponse(BaseModel):
    overall_score: float
    results: list[CompetencyResult]
    top_gaps: list[CompetencyResult]   # sorted by gap, highest first
    strengths: list[CompetencyResult]  # where gap <= 0
    ai_insight: str | None = None
    recommendations_generated: bool = False


_LEVEL_LABELS = {0: "Unassessed", 1: "Beginner", 2: "Basic", 3: "Intermediate", 4: "Advanced"}

# A 5th synthetic bucket for scores >= 90 mapped to level 4 with "Expert" label
def _level_label(level: int, score: float) -> str:
    if level == 4 and score >= 90:
        return "Expert"
    return _LEVEL_LABELS.get(level, "Unassessed")


def _gap_band(gap: int, criticality: float = 1.0) -> str:
    if gap <= 0:
        return "above_required" if gap < 0 else "none"
    weighted = gap * criticality
    if weighted >= 3:
        return "critical"
    if weighted >= 2:
        return "high"
    return "medium"


@router.get(
    "/initial/topics",
    response_model=InitialTopicsResponse,
    summary="Competency topics for the initial assessment",
)
async def initial_topics(
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InitialTopicsResponse:
    """Return competencies to test, based on the user's job role.

    Only competencies that have ≥3 approved questions in the bank are included.
    Returns up to 6 competencies sorted by criticality (highest first).
    """
    from app.models.competency import RoleCompetencyRequirement, Competency
    from app.models.question import Question
    from sqlalchemy import and_

    topics: list[InitialTopicRead] = []

    if user.profile.job_role_id is not None:
        # Load role requirements ordered by criticality descending
        stmt = (
            select(RoleCompetencyRequirement, Competency)
            .join(Competency, Competency.id == RoleCompetencyRequirement.competency_id)
            .where(RoleCompetencyRequirement.job_role_id == user.profile.job_role_id)
            .order_by(RoleCompetencyRequirement.criticality.desc())
        )
        requirements = (await session.execute(stmt)).all()

        for req, comp in requirements:
            # Count approved questions
            q_count = await session.scalar(
                select(func.count())
                .select_from(Question)
                .where(and_(
                    Question.competency_id == comp.id,
                    Question.status == "APPROVED",
                    Question.is_negative_example.is_(False),
                ))
            )
            if (q_count or 0) < 3:
                continue

            topics.append(InitialTopicRead(
                competency_id=comp.id,
                competency_code=comp.code,
                competency_name=comp.name,
                cluster=comp.cluster,
                required_level=req.required_level,
                question_count=min(int(q_count), 5),
                criticality=float(req.criticality),
            ))

            if len(topics) >= 6:
                break

    # Fallback: if job role has no requirements or no questions, pick SQL
    if not topics:
        from app.models.question import Question
        stmt2 = (
            select(Competency)
            .join(Question, Question.competency_id == Competency.id)
            .where(Question.status == "APPROVED")
            .where(Question.is_negative_example.is_(False))
            .group_by(Competency.id)
            .having(func.count() >= 3)
            .limit(5)
        )
        fallback_comps = (await session.execute(stmt2)).scalars().all()
        for comp in fallback_comps:
            q_count = await session.scalar(
                select(func.count()).select_from(Question)
                .where(Question.competency_id == comp.id)
                .where(Question.status == "APPROVED")
            )
            topics.append(InitialTopicRead(
                competency_id=comp.id,
                competency_code=comp.code,
                competency_name=comp.name,
                cluster=comp.cluster,
                required_level=3,
                question_count=min(int(q_count or 0), 5),
                criticality=1.0,
            ))

    total = sum(t.question_count for t in topics)
    return InitialTopicsResponse(topics=topics, total_questions=total)


@router.post(
    "/initial/start",
    response_model=InitialStartResponse,
    summary="Start all assessment sessions for the initial assessment",
)
async def initial_start(
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InitialStartResponse:
    """Create one assessment per topic returned by /initial/topics.

    Each assessment is created in 'proctored' mode so the evidence carries
    0.90 confidence and supersedes the 0.25 self-declarations from onboarding.
    Returns a list of {competency, assessment_id} so the frontend can drive
    each quiz in sequence.
    """
    topics_resp = await initial_topics(user=user, session=session)
    refs: list[StartedAssessmentRef] = []

    for topic in topics_resp.topics:
        assessment = await service.create_assessment(
            session,
            user_id=user.id,
            competency_id=topic.competency_id,
            material_id=None,
            count=topic.question_count,
            mode="proctored",
        )
        session.add(ActivityLog(
            user_id=user.id,
            action="initial_assessment.start",
            entity="assessments",
            entity_id=assessment.id,
            extra={"competency_code": topic.competency_code, "count": topic.question_count},
        ))
        refs.append(StartedAssessmentRef(
            competency_id=topic.competency_id,
            competency_code=topic.competency_code,
            competency_name=topic.competency_name,
            assessment_id=assessment.id,
            question_count=topic.question_count,
        ))

    await session.commit()
    return InitialStartResponse(
        assessments=refs,
        total_questions=sum(r.question_count for r in refs),
    )


@router.post(
    "/initial/complete",
    response_model=InitialCompleteResponse,
    summary="Finalise the initial assessment and generate recommendations",
)
async def initial_complete(
    payload: InitialCompleteRequest,
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InitialCompleteResponse:
    """Aggregate submitted assessment results, mark profile as assessed, generate recommendations.

    Must be called AFTER each assessment in payload.assessment_ids has been
    submitted via POST /assessments/{id}/submit.
    """
    from app.models.assessment import Assessment
    from app.models.competency import RoleCompetencyRequirement, Competency
    from app.services import m5_recommender as recommender
    from app.services.m2_framework import load_requirements
    from app.models.user import Profile

    results: list[CompetencyResult] = []

    # Load required levels for the user's role
    req_map: dict[str, int] = {}
    crit_map: dict[str, float] = {}
    if user.profile.job_role_id:
        for req, comp in await load_requirements(session, user.profile.job_role_id):
            req_map[str(comp.id)] = req.required_level
            crit_map[str(comp.id)] = float(req.criticality)

    for assessment_id in payload.assessment_ids:
        assessment = await session.get(Assessment, assessment_id)
        if assessment is None or assessment.user_id != user.id:
            continue
        if assessment.score is None or assessment.level_after is None:
            continue  # not yet submitted — skip

        comp = assessment.competency
        if comp is None:
            continue

        score_pct = float(assessment.score)
        level_after = int(assessment.level_after)
        level_before = int(assessment.level_before or 0)
        correct = int(assessment.correct_count or 0)
        total = int(assessment.total_questions)
        comp_id_str = str(comp.id)
        req_level = req_map.get(comp_id_str, 3)
        criticality = crit_map.get(comp_id_str, 1.0)
        gap = req_level - level_after

        results.append(CompetencyResult(
            competency_id=comp.id,
            competency_code=comp.code,
            competency_name=comp.name,
            score=score_pct,
            correct=correct,
            total=total,
            level_before=level_before,
            level_after=level_after,
            level_label=_level_label(level_after, score_pct),
            required_level=req_level,
            required_label=_LEVEL_LABELS.get(req_level, "Advanced"),
            gap=gap,
            gap_band=_gap_band(gap, criticality),
        ))

    # Overall score = weighted average
    overall = (sum(r.score for r in results) / len(results)) if results else 0.0

    # Sort gaps: highest gap first
    gaps = sorted([r for r in results if r.gap > 0], key=lambda r: r.gap, reverse=True)
    strengths = [r for r in results if r.gap <= 0]

    # Best-effort AI insight
    ai_insight: str | None = None
    try:
        from app.ai.llm_client import complete
        from app.ai import prompts
        competency_summary = "\n".join(
            f"- {r.competency_name}: {r.score:.0f}% ({r.level_label}) — required: {r.required_label}"
            for r in results
        )
        gap_summary = "\n".join(
            f"- {r.competency_name}: {r.gap_band} gap"
            for r in gaps[:3]
        ) or "No significant gaps identified."
        prompt = (
            f"You are an expert learning advisor for Indian government officials.\n"
            f"Role: {user.profile.designation or 'Statistical Officer'}\n\n"
            f"Initial competency assessment results:\n{competency_summary}\n\n"
            f"Top gaps:\n{gap_summary}\n\n"
            f"Write a 3-sentence personalised insight: summarise strengths (1 sentence), "
            f"top priorities for development (1 sentence), and one encouraging message (1 sentence). "
            f"Be specific. Do not use bullet points."
        )
        ai_insight = await complete(prompt, max_tokens=180)
    except Exception:
        if gaps:
            top_gap = gaps[0]
            ai_insight = (
                f"Your assessment reveals strong performance in "
                f"{strengths[0].competency_name if strengths else 'several areas'}. "
                f"Your highest development priority is {top_gap.competency_name}, "
                f"where a {top_gap.gap_band} gap exists. "
                f"Focusing on the recommended courses will accelerate your growth."
            )
        else:
            ai_insight = (
                "Excellent! Your assessment shows you meet or exceed the required competency "
                "levels. Continue deepening your expertise with advanced courses."
            )

    # Mark profile as assessment-complete
    profile = await session.get(Profile, user.id)
    if profile is not None:
        profile.initial_assessment_completed = True
        session.add(ActivityLog(
            user_id=user.id,
            action="initial_assessment.complete",
            entity="profile",
            entity_id=user.id,
            extra={"overall_score": round(overall, 1), "competencies_tested": len(results)},
        ))

    # Generate recommendations now that we have real evidence
    rec_ok = False
    try:
        await recommender.generate(session, profile=user.profile)
        rec_ok = True
    except Exception:
        pass  # recommendations will be generated on first visit to /recommendations

    await session.commit()

    return InitialCompleteResponse(
        overall_score=round(overall, 1),
        results=results,
        top_gaps=gaps[:3],
        strengths=strengths,
        ai_insight=ai_insight,
        recommendations_generated=rec_ok,
    )

