"""M5 · Recommendation Engine — database work and orchestration.

Decision layer. Retrieve wide, rank on policy, sequence against a calendar.
Blends iGOT self-paced courses with NSSTA TPAC-approved programmes.

The arithmetic lives in ``m5_ranking`` as pure functions; this module loads the
inputs, runs the three stages, asks the model for an explanation, and persists
the batch. Only the explanation involves a language model, and it runs after
the order is already fixed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import embeddings, prompts, scrub
from app.ai.llm_client import complete
from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import get_logger
from app.models.course import Course, Enrollment, Recommendation
from app.models.user import Profile
from app.services import m2_framework as framework
from app.services import m4_gap_engine as engine
from app.services import m5_ranking as ranking

log = get_logger(__name__)

#: Stage 1 retrieves wide — the ranker is what narrows, not the retriever.
RETRIEVE_PER_GAP = 100
DENSE_MIN_SIMILARITY = 0.20
MAX_TARGET_GAPS = 5

# Re-exported so callers and tests have one place to read the weights from.
WEIGHTS = ranking.WEIGHTS


@dataclass
class Candidate:
    """An offering under consideration, bound to the gap that surfaced it."""

    offering: ranking.Offering
    gap: engine.GapRow
    dense_similarity: float = 0.0
    fusion_score: float = 0.0
    prerequisites_met: bool = True
    terms: dict[str, float] = field(default_factory=dict)
    final_score: float = 0.0

    @property
    def course_id(self) -> uuid.UUID:
        return uuid.UUID(self.offering.course_id)


@dataclass
class ScoredRecommendation:
    """A ranked candidate with its explanation and pathway placement."""

    rank: int
    candidate: Candidate
    explanation: str
    explanation_source: str
    ai_context: dict[str, Any]
    model: str | None
    step: ranking.PathwayStep | None = None


# ── Stage 1 · retrieval ──────────────────────────────────────────────────────


async def _dense_retrieve(
    session: AsyncSession, query: str, limit: int
) -> list[tuple[str, float]]:
    """Semantic neighbours, by cosine distance over the HNSW index."""
    vector = embeddings.embed_one(query)
    rows = (
        await session.execute(
            text(
                "select course_id, similarity from match_courses("
                "cast(:emb as vector(384)), :match_count, :min_similarity)"
            ),
            {
                "emb": embeddings.to_pgvector(vector),
                "match_count": limit,
                "min_similarity": DENSE_MIN_SIMILARITY,
            },
        )
    ).all()
    return [(str(course_id), float(similarity)) for course_id, similarity in rows]


async def _lexical_retrieve(
    session: AsyncSession, query: str, limit: int
) -> list[tuple[str, float]]:
    """Exact terms and rare tokens — precisely what an embedding is worst at.

    "SDMX", "PLFS", "GROUP BY" are the kind of token a dense model smooths
    away and a text index nails.
    """
    rows = (
        await session.execute(
            text(
                "select id, ts_rank(search_tsv, plainto_tsquery('english', :q)) as rank "
                "from courses "
                "where status = 'ACTIVE' "
                "  and search_tsv @@ plainto_tsquery('english', :q) "
                "order by rank desc limit :k"
            ),
            {"q": query, "k": limit},
        )
    ).all()
    return [(str(course_id), float(rank)) for course_id, rank in rows]


async def _tag_retrieve(
    session: AsyncSession, competency_code: str, limit: int
) -> list[tuple[str, float]]:
    """Exact competency-code match, via the catalogue's own tagging."""
    rows = (
        await session.execute(
            select(Course.id)
            .where(Course.status == "ACTIVE")
            .where(Course.competency_code == competency_code)
            .order_by(Course.proficiency_level)
            .limit(limit)
        )
    ).all()
    return [(str(course_id), 1.0) for (course_id,) in rows]


async def retrieve_for_gap(
    session: AsyncSession, gap: engine.GapRow
) -> tuple[dict[str, float], dict[str, float]]:
    """Three retrievers, fused by reciprocal rank.

    Returns (fused score by course id, dense similarity by course id). The
    dense similarity is kept separately because it is a ranking term in its own
    right — fusion decides *what* is considered, similarity is one input to
    *how highly* it ranks.
    """
    query = f"{gap.competency_name}. {gap.competency_description}".strip()

    dense = await _dense_retrieve(session, query, RETRIEVE_PER_GAP)
    lexical = await _lexical_retrieve(session, gap.competency_name, RETRIEVE_PER_GAP)
    tagged = await _tag_retrieve(session, gap.competency_code, RETRIEVE_PER_GAP)

    rankings = [
        [ranking.RankedHit(cid, i + 1, s) for i, (cid, s) in enumerate(dense)],
        [ranking.RankedHit(cid, i + 1, s) for i, (cid, s) in enumerate(lexical)],
        [ranking.RankedHit(cid, i + 1, s) for i, (cid, s) in enumerate(tagged)],
    ]
    fused = ranking.normalise_fusion(ranking.reciprocal_rank_fusion(rankings))
    return fused, dict(dense)


def _to_offering(course: Course, *, now: datetime) -> ranking.Offering:
    synced = course.synced_at or now
    if synced.tzinfo is None:
        synced = synced.replace(tzinfo=timezone.utc)
    return ranking.Offering(
        course_id=str(course.id),
        external_id=course.external_id,
        source=course.source,
        title=course.title,
        competency_code=course.competency_code,
        proficiency_level=course.proficiency_level,
        duration_hours=course.duration_hours,
        learning_format=course.learning_format,
        prerequisites=list(course.prerequisites or []),
        session_start=course.session_start,
        seats=course.seats,
        synced_days_ago=max(0, (now - synced).days),
    )


async def _completed_course_ids(
    session: AsyncSession, user_id: uuid.UUID
) -> set[str]:
    rows = await session.execute(
        select(Enrollment.course_id)
        .where(Enrollment.user_id == user_id)
        .where(Enrollment.status == "COMPLETED")
    )
    return {str(cid) for cid in rows.scalars().all()}


# ── the AI context ───────────────────────────────────────────────────────────


def build_ai_context(
    profile: Profile, job_role_title: str, candidate: Candidate
) -> dict[str, Any]:
    """Assemble the anonymised context for the explanation.

    Whitelist-only. Nothing here identifies a person: years of experience is
    coarsened to a band, and no name, email, employee code or identifier is
    included. This exact dict is stored and returned by the breakdown endpoint,
    so what the interface shows is what actually left the process.
    """
    return scrub.build_context(
        job_role_title=job_role_title,
        competency_name=candidate.gap.competency_name,
        competency_code=candidate.gap.competency_code,
        current_level=candidate.gap.current_level,
        required_level=candidate.gap.required_level,
        gap=candidate.gap.gap,
        gap_band=candidate.gap.band.value,
        frac_current=candidate.gap.frac_current,
        frac_required=candidate.gap.frac_required,
        years_experience_band=scrub.experience_band(profile.years_experience),
        course_title=candidate.offering.title,
        course_level=candidate.offering.proficiency_level,
        course_duration_hours=candidate.offering.duration_hours,
        course_format=candidate.offering.learning_format,
        provider=candidate.offering.source,
    )


def template_explanation(context: dict[str, Any]) -> str:
    """The non-AI fallback. A card is never left empty."""
    return prompts.FALLBACK_RECOMMENDATION.format(
        competency_name=context["competency_name"],
        current_level=context["current_level"],
        required_level=context["required_level"],
        job_role_title=context["job_role_title"],
        course_duration_hours=context["course_duration_hours"],
        course_format=str(context["course_format"]).replace("_", "-").lower(),
        proficiency=context["course_level"],
    )


async def explain(
    session: AsyncSession, *, context: dict[str, Any], user_id: uuid.UUID
) -> tuple[str, str, str | None]:
    """Ask the model for an explanation, falling back to a template.

    Returns (text, source, model). The source travels to the interface because
    presenting a templated sentence as model output would be dishonest.
    """
    prompt = prompts.RECOMMENDATION.format(
        job_role_title=context["job_role_title"],
        required_level=context["required_level"],
        competency_name=context["competency_name"],
        frac_required=context["frac_required"],
        current_level=context["current_level"],
        frac_current=context["frac_current"],
        gap_band=context["gap_band"],
        course_title=context["course_title"],
        proficiency=context["course_level"],
        course_duration_hours=context["course_duration_hours"],
        course_format=context["course_format"],
        provider=context["provider"],
    )
    try:
        result = await complete(
            session=session,
            purpose="explanation",
            prompt=prompt,
            system=prompts.SYSTEM_RECOMMENDATION,
            user_id=user_id,
            temperature=0.4,
            max_tokens=700,
        )
        text_out = result if isinstance(result, str) else str(result)
        if text_out.strip():
            return text_out.strip(), "ai", settings.MODEL_TEXT
    except AppError as exc:
        log.info("explanation fell back to template: %s", exc.message)
    except Exception as exc:  # noqa: BLE001 - never fail a recommendation on this
        log.warning("unexpected explanation failure: %s", exc)

    return template_explanation(context), "template", None


# ── the three stages ─────────────────────────────────────────────────────────


async def generate(
    session: AsyncSession,
    *,
    profile: Profile,
    limit: int = 5,
    max_per_competency: int = ranking.MAX_PER_COMPETENCY,
    monthly_hours: int = ranking.DEFAULT_MONTHLY_HOURS,
    explain_with_llm: bool = True,
) -> tuple[uuid.UUID, list[ScoredRecommendation]]:
    """Produce and persist one ranked, sequenced recommendation batch."""
    now = datetime.now(tz=timezone.utc)
    batch_id = uuid.uuid4()

    if profile.job_role_id is None:
        return batch_id, []

    requirements = await framework.load_requirement_specs(session, profile.job_role_id)
    observations = await framework.load_observations(session, profile.id)
    gap_rows = engine.build_gap_rows(requirements, observations, now=now)
    targets = engine.target_gaps(gap_rows, limit=MAX_TARGET_GAPS)
    if not targets:
        log.info("no open gaps for %s; empty recommendation batch", profile.id)
        return batch_id, []

    max_priority = max((g.priority for g in targets), default=1.0) or 1.0

    # ── Stage 1 · retrieve, per gap, and merge ───────────────────────────────
    by_course: dict[str, Candidate] = {}
    for gap in targets:
        fused, dense = await retrieve_for_gap(session, gap)
        if not fused:
            continue
        courses = (
            await session.execute(
                select(Course).where(Course.id.in_([uuid.UUID(c) for c in fused]))
            )
        ).scalars().all()

        for course in courses:
            key = str(course.id)
            similarity = dense.get(key, 0.0)
            existing = by_course.get(key)
            if existing is None:
                by_course[key] = Candidate(
                    offering=_to_offering(course, now=now),
                    gap=gap,
                    dense_similarity=similarity,
                    fusion_score=fused.get(key, 0.0),
                )
            elif fused.get(key, 0.0) > existing.fusion_score:
                # A course can be surfaced by more than one gap. Attribute it
                # to whichever gap matched it most strongly, so the explanation
                # talks about the right competency.
                existing.gap = gap
                existing.dense_similarity = similarity
                existing.fusion_score = fused.get(key, 0.0)

    # ── Stage 2 · rank ───────────────────────────────────────────────────────
    completed = await _completed_course_ids(session, profile.id)
    levels_by_code = await framework.load_current_levels_by_code(session, profile.id)

    _pinned, rankable = ranking.apply_hard_constraints(
        [c.offering for c in by_course.values()], completed_ids=completed
    )
    rankable_ids = {o.course_id for o in rankable}

    scored: list[tuple[float, ranking.Offering, str]] = []
    for key, candidate in by_course.items():
        if key not in rankable_ids:
            continue
        candidate.prerequisites_met = engine.prerequisites_satisfied(
            candidate.offering.prerequisites, levels_by_code
        )
        final, terms = ranking.score_offering(
            candidate.offering,
            gap_priority_normalised=candidate.gap.priority / max_priority,
            similarity=candidate.dense_similarity,
            current_level=candidate.gap.current_level,
            prerequisites_met=candidate.prerequisites_met,
            monthly_hours=monthly_hours,
        )
        candidate.final_score = final
        candidate.terms = terms
        scored.append((final, candidate.offering, candidate.gap.competency_code))

    # Sort by score, then external id, so equal scores do not shuffle between
    # requests — a demonstration that reorders on refresh looks broken.
    scored.sort(key=lambda entry: (-entry[0], entry[1].external_id))
    scored = ranking.cap_per_competency(scored, max_per_competency=max_per_competency)
    top = scored[:limit]
    top_candidates = [by_course[offering.course_id] for _score, offering, _code in top]

    # ── Stage 3 · sequence ───────────────────────────────────────────────────
    ordered = ranking.topological_order(
        [c.offering for c in top_candidates], levels_by_code
    )
    steps = ranking.place_on_calendar(
        ordered, start=date.today(), monthly_hours=monthly_hours
    )
    step_by_course = {step.offering.course_id: step for step in steps}

    # ── persist, and explain ─────────────────────────────────────────────────
    job_role = await framework.resolve_job_role_for_user(session, profile)
    job_role_title = job_role.title if job_role else "Statistical Officer"

    out: list[ScoredRecommendation] = []
    for rank, candidate in enumerate(top_candidates, start=1):
        context = build_ai_context(profile, job_role_title, candidate)
        if explain_with_llm:
            text_out, source, model = await explain(
                session, context=context, user_id=profile.id
            )
        else:
            text_out, source, model = template_explanation(context), "template", None

        step = step_by_course.get(candidate.offering.course_id)
        session.add(
            Recommendation(
                batch_id=batch_id,
                user_id=profile.id,
                course_id=candidate.course_id,
                competency_id=uuid.UUID(candidate.gap.competency_id),
                rank=rank,
                score=Decimal(str(round(candidate.final_score, 4))),
                breakdown={
                    **candidate.terms,
                    "weights": dict(ranking.WEIGHTS),
                    "final_score": candidate.final_score,
                    "fusion_score": round(candidate.fusion_score, 4),
                    "retrievers": ["dense_pgvector", "lexical_bm25", "tag_match"],
                    "fusion": f"reciprocal rank, k={ranking.RRF_K}",
                    "ai_context_sent": context,
                    "explanation_source": source,
                    "model": model,
                    "competency_code": candidate.gap.competency_code,
                    "competency_name": candidate.gap.competency_name,
                    "current_level": candidate.gap.current_level,
                    "required_level": candidate.gap.required_level,
                    "gap_band": candidate.gap.band.value,
                    "gap_derivation": candidate.gap.derivation,
                    "sequence": (
                        {
                            "order": step.order,
                            "starts_on": step.starts_on.isoformat(),
                            "ends_on": step.ends_on.isoformat(),
                            "months_required": step.months_required,
                            "anchored": step.anchored,
                        }
                        if step
                        else None
                    ),
                },
                explanation=text_out,
            )
        )
        out.append(
            ScoredRecommendation(
                rank=rank,
                candidate=candidate,
                explanation=text_out,
                explanation_source=source,
                ai_context=context,
                model=model,
                step=step,
            )
        )

    await session.flush()
    log.info(
        "recommendation batch %s: %d candidates -> %d ranked (%d AI explanations)",
        batch_id,
        len(by_course),
        len(out),
        sum(1 for r in out if r.explanation_source == "ai"),
    )
    return batch_id, out


async def load_courses(
    session: AsyncSession, course_ids: list[uuid.UUID]
) -> dict[uuid.UUID, Course]:
    if not course_ids:
        return {}
    rows = (
        await session.execute(select(Course).where(Course.id.in_(course_ids)))
    ).scalars().all()
    return {c.id: c for c in rows}


async def latest_batch_id(
    session: AsyncSession, user_id: uuid.UUID
) -> uuid.UUID | None:
    return await session.scalar(
        select(Recommendation.batch_id)
        .where(Recommendation.user_id == user_id)
        .order_by(func.max(Recommendation.created_at).desc())
        .group_by(Recommendation.batch_id)
        .limit(1)
    )
