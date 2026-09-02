"""M3 · assessment orchestration and the closed loop.

Measurement layer. Adaptive delivery, deterministic scoring, evidence written
at the confidence the delivery mode warrants.

The scoring rules live in ``m3_scoring`` as pure functions. This module owns
the database work around them: building a blueprint, selecting items, recording
responses, and running the submit sequence.

The loop:

    1. score                    difficulty-weighted, deterministic
    2. level_before             from the evidence ledger
    3. level_after              SME cut-scores, never decreasing
    4. append competency_evidence
    5. recompute the gap        M4
    6. regenerate recommendations M5
    7. LLM feedback on weak topics — best effort, after the commit

Steps 1–6 succeed or roll back together. Step 7 runs afterwards and can never
fail the request; if the model is unavailable a templated sentence is stored
and the response says which it was.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import prompts
from app.ai.llm_client import complete
from app.core.errors import AppError, ConflictError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models.architecture import FrameworkVersion
from app.models.assessment import Assessment, AssessmentQuestion
from app.models.competency import Competency
from app.models.question import Question
from app.models.user import Profile
from app.services import m2_framework as framework
from app.services import m3_scoring as scoring
from app.services import m4_gap_engine as engine
from app.services import m5_recommender as recommender
from app.services import m9_events as events

log = get_logger(__name__)

#: Blueprint: the difficulty spread a paper aims for, as fractions of the item
#: budget. Coverage per competency and item budget travel with the assessment
#: so the paper served can be reconstructed.
DIFFICULTY_MIX = {"easy": 0.3, "medium": 0.4, "hard": 0.3}


async def _select_items(
    session: AsyncSession,
    *,
    competency_id: uuid.UUID,
    material_id: uuid.UUID | None,
    count: int,
) -> list[Question]:
    """Choose approved items against the blueprint.

    Only APPROVED items are ever served — draft and rejected items exist for
    the trainer's review and never reach an officer. Within each difficulty
    band, items least recently served are preferred, which rotates the pool
    and is the cheap half of the integrity controls.
    """
    stmt = (
        select(Question)
        .where(Question.competency_id == competency_id)
        .where(Question.status == "APPROVED")
        .where(Question.is_negative_example.is_(False))
    )
    if material_id is not None:
        stmt = stmt.where(Question.material_id == material_id)

    pool = list((await session.execute(stmt)).scalars().all())
    if not pool:
        raise ConflictError(
            "There are no approved questions for this competency yet. A trainer "
            "needs to upload material and approve generated questions first."
        )

    by_difficulty: dict[str, list[Question]] = {"easy": [], "medium": [], "hard": []}
    for question in pool:
        by_difficulty.setdefault(question.difficulty, []).append(question)

    rng = random.Random()
    for bucket in by_difficulty.values():
        # Pool rotation: least-served first, then random within that.
        rng.shuffle(bucket)
        bucket.sort(key=lambda q: q.times_served)

    picked: list[Question] = []
    for difficulty, share in DIFFICULTY_MIX.items():
        wanted = round(count * share)
        picked.extend(by_difficulty.get(difficulty, [])[:wanted])

    if len(picked) < count:
        chosen = {q.id for q in picked}
        remainder = [q for q in pool if q.id not in chosen]
        remainder.sort(key=lambda q: q.times_served)
        picked.extend(remainder[: count - len(picked)])

    rng.shuffle(picked)
    return picked[:count]


def _build_blueprint(items: list[Question], competency_code: str) -> dict:
    """What was actually served, recorded alongside the result."""
    spread: dict[str, int] = {}
    for item in items:
        spread[item.difficulty] = spread.get(item.difficulty, 0) + 1
    return {
        "competency": competency_code,
        "item_budget": len(items),
        "difficulty_spread": spread,
        "target_mix": DIFFICULTY_MIX,
        "weights": dict(scoring.DIFFICULTY_WEIGHT),
    }


async def create_assessment(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    competency_id: uuid.UUID,
    material_id: uuid.UUID | None,
    count: int,
    mode: str = "practice",
) -> Assessment:
    competency = await session.get(Competency, competency_id)
    if competency is None:
        raise NotFoundError("No such competency.")

    items = await _select_items(
        session, competency_id=competency_id, material_id=material_id, count=count
    )
    version = await framework.current_framework_version(session)

    assessment = Assessment(
        user_id=user_id,
        competency_id=competency_id,
        material_id=material_id,
        status="IN_PROGRESS",
        total_questions=len(items),
        mode=mode,
        blueprint=_build_blueprint(items, competency.code),
        framework_version_id=version.id if version else None,
    )
    session.add(assessment)
    await session.flush()

    for position, item in enumerate(items, start=1):
        session.add(
            AssessmentQuestion(
                assessment_id=assessment.id, question_id=item.id, position=position
            )
        )

    await session.flush()
    await events.emit(
        session,
        verb=events.Verb.ASSESSMENT_STARTED,
        actor_id=user_id,
        object_type="assessment",
        object_id=assessment.id,
        payload={"competency": competency.code, "items": len(items), "mode": mode},
    )
    log.info(
        "assessment %s created: %d items for %s (%s)",
        assessment.id,
        len(items),
        competency.code,
        mode,
    )
    return assessment


async def load_assessment(
    session: AsyncSession, assessment_id: uuid.UUID, user_id: uuid.UUID
) -> Assessment:
    assessment = await session.get(Assessment, assessment_id)
    if assessment is None:
        raise NotFoundError("No such assessment.")
    if assessment.user_id != user_id:
        raise ForbiddenError("That assessment belongs to another officer.")
    return assessment


async def load_items(
    session: AsyncSession, assessment_id: uuid.UUID
) -> list[tuple[AssessmentQuestion, Question]]:
    rows = await session.execute(
        select(AssessmentQuestion, Question)
        .join(Question, Question.id == AssessmentQuestion.question_id)
        .where(AssessmentQuestion.assessment_id == assessment_id)
        .order_by(AssessmentQuestion.position)
    )
    return [tuple(r) for r in rows.all()]  # type: ignore[misc]


async def record_answer(
    session: AsyncSession,
    *,
    assessment: Assessment,
    question_id: uuid.UUID,
    selected_index: int,
) -> int:
    """Store a selection. Idempotent: re-answering replaces the choice.

    Correctness is deliberately not evaluated here and not returned. Marking
    happens at submit time so an officer cannot probe the answer key one
    option at a time.
    """
    if assessment.status != "IN_PROGRESS":
        raise ConflictError("This assessment has already been submitted.")

    row = await session.get(AssessmentQuestion, (assessment.id, question_id))
    if row is None:
        raise NotFoundError("That question is not part of this assessment.")

    row.selected_index = selected_index
    await session.flush()

    answered = await session.scalar(
        select(func.count())
        .select_from(AssessmentQuestion)
        .where(AssessmentQuestion.assessment_id == assessment.id)
        .where(AssessmentQuestion.selected_index.isnot(None))
    )
    return int(answered or 0)


async def _feedback(
    session: AsyncSession,
    *,
    competency_name: str,
    score: float,
    correct_count: int,
    total_questions: int,
    weak: list[str],
    strong: list[str],
    user_id: uuid.UUID,
) -> tuple[str, str]:
    """Ask the model to name a misconception, after scoring.

    The model reads the response pattern; it never produces or adjusts the
    number. Returns (text, source). Never raises — this is step 7.
    """
    template = (
        prompts.FALLBACK_FEEDBACK_WITH_TOPICS.format(
            correct_count=correct_count,
            total_questions=total_questions,
            weak_topics=", ".join(weak),
            competency_name=competency_name,
        )
        if weak
        else prompts.FALLBACK_FEEDBACK_CLEAN.format(
            correct_count=correct_count,
            total_questions=total_questions,
            competency_name=competency_name,
        )
    )

    try:
        from app.ai import scrub

        context = scrub.build_context(
            competency_name=competency_name,
            score=score,
            correct_count=correct_count,
            total_questions=total_questions,
            weak_topics=", ".join(weak) if weak else "none",
            strong_topics=", ".join(strong) if strong else "none recorded",
        )
        result = await complete(
            session=session,
            purpose="feedback",
            prompt=prompts.FEEDBACK.format(**context),
            system=prompts.SYSTEM_FEEDBACK,
            user_id=user_id,
            temperature=0.4,
            max_tokens=220,
        )
        text = result if isinstance(result, str) else str(result)
        if text.strip():
            return text.strip(), "ai"
    except AppError as exc:
        log.info("feedback fell back to template: %s", exc.message)
    except Exception as exc:  # noqa: BLE001
        log.warning("unexpected feedback failure: %s", exc)

    return template, "template"


class SubmitResult:
    """Everything the result screen needs, assembled by :func:`submit`."""

    def __init__(self, **kwargs: object) -> None:
        self.__dict__.update(kwargs)


async def submit(
    session: AsyncSession, *, assessment: Assessment, profile: Profile
) -> SubmitResult:
    """Run the closed loop. Steps 1–6 inside the caller's transaction."""
    if assessment.status != "IN_PROGRESS":
        raise ConflictError("This assessment has already been submitted.")

    items = await load_items(session, assessment.id)
    if not items:
        raise ConflictError("This assessment has no questions.")

    competency = await session.get(Competency, assessment.competency_id)
    if competency is None:
        raise NotFoundError("The competency for this assessment no longer exists.")

    # ── 1 · score, difficulty-weighted and deterministic ─────────────────────
    answers = [
        scoring.AnsweredQuestion(
            question_id=str(question.id),
            correct_index=question.correct_index,
            selected_index=row.selected_index,
            difficulty=question.difficulty,
            topic=question.topic,
        )
        for row, question in items
    ]
    breakdown = scoring.score_assessment(answers)
    weak = scoring.weak_topics(answers)
    strong = scoring.strong_topics(answers)

    for row, question in items:
        correct = (
            row.selected_index is not None
            and row.selected_index == question.correct_index
        )
        row.is_correct = correct
        # Item calibration: difficulty is learned from live responses, and the
        # observed value eventually replaces the authored estimate.
        if row.selected_index is not None:
            question.times_served += 1
            if correct:
                question.times_correct += 1

    # ── 2 · level before, from the evidence ledger ───────────────────────────
    observations = await framework.load_observations(session, profile.id)
    before = observations.get(str(competency.id), engine.Observation())
    level_before = before.level

    # ── 3 · level after, from SME cut-scores ────────────────────────────────
    cut_scores = await framework.load_cut_scores(session, competency.id)
    level_after = scoring.next_level(
        level_before, breakdown.weighted_score, breakdown.attempted, cut_scores
    )
    revisit = scoring.needs_revisit(breakdown.weighted_score, cut_scores)
    confidence = scoring.confidence_for_mode(assessment.mode)

    requirements = await framework.load_requirement_specs(session, profile.job_role_id)  # type: ignore[arg-type]
    requirement = next(
        (r for r in requirements if r.competency_id == str(competency.id)), None
    )
    required_level = requirement.required_level if requirement else level_before + 1
    criticality = requirement.criticality if requirement else 1.0
    horizon = requirement.horizon if requirement else "current_role"

    # ── 4 · append the evidence row ─────────────────────────────────────────
    evidence = await framework.record_evidence(
        session,
        user_id=profile.id,
        competency_id=competency.id,
        level=level_after,
        source_type="assessment",
        source_ref=assessment.id,
        score=breakdown.weighted_score,
        confidence=confidence,
        note=(
            f"{assessment.mode.title()} assessment {assessment.id}: "
            f"{breakdown.correct}/{breakdown.attempted} correct, "
            f"weighted {breakdown.weighted_score}%."
            + (" Marked for revisit." if revisit else "")
        ),
    )

    assessment.status = "SUBMITTED"
    assessment.correct_count = breakdown.correct
    assessment.score = Decimal(str(breakdown.raw_score))
    assessment.weighted_score = Decimal(str(breakdown.weighted_score))
    assessment.level_before = level_before
    assessment.level_after = level_after
    assessment.submitted_at = datetime.now(tz=timezone.utc)
    await session.flush()

    # ── 5 · recompute the gap ───────────────────────────────────────────────
    gap_before = engine.compute_gap(required_level, level_before)
    gap_after = engine.compute_gap(required_level, level_after)
    band_before = engine.band_for(
        gap_before,
        criticality=criticality,
        horizon=horizon,
        current_level=level_before,
        required_level=required_level,
    )
    band_after = engine.band_for(
        gap_after,
        criticality=criticality,
        horizon=horizon,
        current_level=level_after,
        required_level=required_level,
    )
    priority_before = engine.priority_for(
        gap_before, criticality, before.confidence, horizon
    )
    priority_after = engine.priority_for(gap_after, criticality, confidence, horizon)

    # ── 6 · regenerate recommendations against the updated ledger ───────────
    batch_id, ranked = await recommender.generate(
        session, profile=profile, limit=5, explain_with_llm=False
    )

    await events.emit(
        session,
        verb=events.Verb.ASSESSMENT_SUBMITTED,
        actor_id=profile.id,
        object_type="assessment",
        object_id=assessment.id,
        payload={
            "competency": competency.code,
            "weighted_score": breakdown.weighted_score,
            "raw_score": breakdown.raw_score,
            "attempted": breakdown.attempted,
            "mode": assessment.mode,
        },
    )
    if level_after != level_before:
        await events.emit(
            session,
            verb=events.Verb.COMPETENCY_LEVEL_CHANGED,
            actor_id=profile.id,
            object_type="competency",
            object_id=competency.id,
            payload={
                "from": level_before,
                "to": level_after,
                "source": "assessment",
                "confidence": confidence,
            },
        )

    return SubmitResult(
        assessment=assessment,
        competency=competency,
        breakdown=breakdown,
        score=breakdown.weighted_score,
        raw_score=breakdown.raw_score,
        correct_count=breakdown.correct,
        attempted=breakdown.attempted,
        total_questions=len(answers),
        mode=assessment.mode,
        confidence=confidence,
        cut_scores=cut_scores,
        level_before=level_before,
        level_after=level_after,
        required_level=required_level,
        criticality=criticality,
        gap_before=gap_before,
        gap_after=gap_after,
        band_before=band_before.value,
        band_after=band_after.value,
        priority_before=priority_before,
        priority_after=priority_after,
        frac_before=engine.frac_label(level_before),
        frac_after=engine.frac_label(level_after),
        weak_topics=weak,
        strong_topics=strong,
        revisit=revisit,
        evidence_id=evidence.id,
        batch_id=batch_id,
        recommendations=ranked,
    )


async def add_feedback(
    session: AsyncSession, *, result: SubmitResult, user_id: uuid.UUID
) -> tuple[str, str]:
    """Step 7. Runs after the loop has committed."""
    text, source = await _feedback(
        session,
        competency_name=result.competency.name,  # type: ignore[attr-defined]
        score=result.score,  # type: ignore[attr-defined]
        correct_count=result.correct_count,  # type: ignore[attr-defined]
        total_questions=result.attempted,  # type: ignore[attr-defined]
        weak=result.weak_topics,  # type: ignore[attr-defined]
        strong=result.strong_topics,  # type: ignore[attr-defined]
        user_id=user_id,
    )
    assessment: Assessment = result.assessment  # type: ignore[attr-defined]
    stored = await session.get(Assessment, assessment.id)
    if stored is not None:
        stored.feedback = text
        await session.flush()
    return text, source


async def history(
    session: AsyncSession, user_id: uuid.UUID
) -> list[tuple[Assessment, Competency | None]]:
    rows = await session.execute(
        select(Assessment, Competency)
        .outerjoin(Competency, Competency.id == Assessment.competency_id)
        .where(Assessment.user_id == user_id)
        .order_by(Assessment.started_at.desc())
    )
    return [tuple(r) for r in rows.all()]  # type: ignore[misc]
