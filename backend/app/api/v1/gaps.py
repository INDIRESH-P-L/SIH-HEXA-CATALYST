"""M4 · skill-gap endpoints.

Everything here is deterministic arithmetic performed by the pure functions in
``services/m4_gap_engine.py``. No model is called on any of these paths, and
every row carries the derivation that produced it.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.errors import ConflictError, NotFoundError
from app.core.security import CurrentUser, CurrentUserDep, require_role
from app.models.architecture import GapSnapshot
from app.models.user import Profile
from app.schemas.gap import (
    ActivityRead,
    GapDerivation,
    GapListResponse,
    GapRead,
    GapSummaryRead,
)
from app.services import m2_framework as framework
from app.services import m4_gap_engine as engine

router = APIRouter(prefix="/gaps", tags=["M4 · skill gap"])


def _to_read(row: engine.GapRow) -> GapRead:
    return GapRead(
        competency_id=uuid.UUID(row.competency_id),
        competency_code=row.competency_code,
        competency_name=row.competency_name,
        cluster=row.cluster,
        required_level=row.required_level,
        current_level=row.current_level,
        gap=row.gap,
        band=row.band.value,  # type: ignore[arg-type]
        priority=row.priority,
        criticality=row.criticality,
        horizon=row.horizon,  # type: ignore[arg-type]
        confidence=row.confidence,
        frac_current=row.frac_current,
        frac_required=row.frac_required,
        stale=row.stale,
        source_type=row.source_type,
        assessed_at=row.assessed_at,
        derivation=GapDerivation(**row.derivation) if row.derivation else None,
    )


def _to_summary(summary: engine.GapSummary) -> GapSummaryRead:
    return GapSummaryRead(
        total_competencies=summary.total_competencies,
        critical=summary.critical,
        significant=summary.significant,
        emerging=summary.emerging,
        met=summary.met,
        strength=summary.strength,
        open_gaps=summary.open_gaps,
        top_gaps=[_to_read(r) for r in summary.top_gaps],
        average_current_level=summary.average_current_level,
        average_required_level=summary.average_required_level,
        stale_count=summary.stale_count,
        unassessed_count=summary.unassessed_count,
    )


async def compute_for_user(
    session: AsyncSession, profile: Profile
) -> tuple[list[engine.GapRow], engine.GapSummary]:
    """Load the inputs, then hand them to the pure engine."""
    if profile.job_role_id is None:
        raise ConflictError(
            "This officer has no job role assigned. Position to Role is the "
            "binding every expected competency level derives from, so there is "
            "nothing to measure against until it is set."
        )

    requirements = await framework.load_requirement_specs(session, profile.job_role_id)
    if not requirements:
        raise ConflictError("The assigned job role has no competency requirements defined.")

    observations = await framework.load_observations(session, profile.id)
    rows = engine.build_gap_rows(requirements, observations)
    return rows, engine.summarise(rows)


async def _response(
    session: AsyncSession, profile: Profile
) -> GapListResponse:
    rows, summary = await compute_for_user(session, profile)
    role = await framework.resolve_job_role_for_user(session, profile)
    version = await framework.current_framework_version(session)
    return GapListResponse(
        job_role_code=role.code if role else None,
        job_role_title=role.title if role else None,
        framework_version=version.version if version else None,
        gaps=[_to_read(r) for r in rows],
        summary=_to_summary(summary),
        reassessment_candidates=[
            r.competency_code for r in engine.reassessment_candidates(rows)
        ],
    )


@router.get("/me", response_model=GapListResponse, summary="Your skill gaps, ranked")
async def my_gaps(
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GapListResponse:
    return await _response(session, user.profile)


@router.get(
    "/me/summary",
    response_model=GapSummaryRead,
    summary="Counts per band and your three worst gaps",
)
async def my_gap_summary(
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GapSummaryRead:
    _rows, summary = await compute_for_user(session, user.profile)
    return _to_summary(summary)


@router.get(
    "/me/activities",
    response_model=list[ActivityRead],
    summary="The activities your role performs, and what they require",
)
async def my_activities(
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ActivityRead]:
    """FRAC is Position → Role → Activity → Competency.

    The activity layer is what lets a gap be explained as "you cannot yet do
    this part of your job" rather than as an abstract score.
    """
    if user.profile.job_role_id is None:
        return []
    activities = await framework.load_activities(session, user.profile.job_role_id)
    return [
        ActivityRead(
            id=a.id,
            code=a.code,
            name=a.name,
            description=a.description,
            sequence=a.sequence,
            competency_codes=[
                link.competency.code for link in a.competencies if link.competency
            ],
        )
        for a in activities
    ]


@router.post(
    "/me/snapshot",
    response_model=GapSummaryRead,
    summary="Freeze today's gap analysis against the current framework version",
)
async def take_snapshot(
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GapSummaryRead:
    """Snapshot per (officer, framework version, date).

    So that a dashboard from last quarter recomputes to exactly the same
    numbers, which is the precondition for measuring whether training worked.
    """
    rows, summary = await compute_for_user(session, user.profile)
    version = await framework.current_framework_version(session)
    today = date.today()

    existing = await session.scalar(
        select(GapSnapshot)
        .where(GapSnapshot.user_id == user.id)
        .where(GapSnapshot.taken_on == today)
    )
    payload_rows = [_to_read(r).model_dump(mode="json") for r in rows]
    payload_summary = _to_summary(summary).model_dump(mode="json")

    if existing is None:
        session.add(
            GapSnapshot(
                user_id=user.id,
                framework_version_id=version.id if version else None,
                taken_on=today,
                rows=payload_rows,
                summary=payload_summary,
            )
        )
    else:
        existing.rows = payload_rows
        existing.summary = payload_summary

    await session.commit()
    return _to_summary(summary)


@router.get(
    "/{user_id}",
    response_model=GapListResponse,
    summary="Another officer's gaps (admin)",
)
async def gaps_for_user(
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _actor: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> GapListResponse:
    profile = await session.get(Profile, user_id)
    if profile is None:
        raise NotFoundError("No such officer.")
    return await _response(session, profile)
