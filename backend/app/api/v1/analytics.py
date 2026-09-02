"""M9 · analytics endpoints. Deterministic aggregates, no model involved."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, CurrentUserDep, require_role
from app.schemas.analytics import (
    AdminOverview,
    CompetencyMatrix,
    MyAnalytics,
    TrainingEffectiveness,
)
from app.services import m9_analytics as analytics
from app.services import m9_events as events

router = APIRouter(prefix="/analytics", tags=["M9 · analytics"])

AdminDep = Annotated[CurrentUser, Depends(require_role("admin"))]


@router.get("/me", response_model=MyAnalytics, summary="Your levels, hours and progress")
async def my_analytics(
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MyAnalytics:
    return await analytics.my_analytics(session, user.profile)


@router.get(
    "/admin/overview",
    response_model=AdminOverview,
    summary="Workforce distribution and gap frequency (admin)",
)
async def admin_overview(
    session: Annotated[AsyncSession, Depends(get_session)],
    _actor: AdminDep,
) -> AdminOverview:
    return await analytics.admin_overview(session)


@router.get(
    "/admin/competency-matrix",
    response_model=CompetencyMatrix,
    summary="Role by competency heatmap data (admin)",
)
async def competency_matrix(
    session: Annotated[AsyncSession, Depends(get_session)],
    _actor: AdminDep,
) -> CompetencyMatrix:
    return await analytics.competency_matrix(session)


@router.get(
    "/admin/training-effectiveness",
    response_model=TrainingEffectiveness,
    summary="Level change either side of a course completion (admin)",
)
async def training_effectiveness(
    session: Annotated[AsyncSession, Depends(get_session)],
    _actor: AdminDep,
) -> TrainingEffectiveness:
    return await analytics.training_effectiveness(session)


@router.post(
    "/admin/rebuild-marts",
    summary="Rebuild the analytics marts from current state (admin)",
)
async def rebuild_marts(
    session: Annotated[AsyncSession, Depends(get_session)],
    _actor: AdminDep,
) -> dict[str, int | str]:
    """Run the rollup job.

    In production this runs nightly off the event stream. Exposing it as an
    action means the pipeline can be demonstrated rather than described.
    """
    result = await analytics.rebuild_marts(session)
    await session.commit()
    return {
        **result,
        "note": (
            "Dashboards read marts, marts rebuild from events, and an event is "
            "never edited. That is what makes every figure reconcilable."
        ),
    }


@router.get("/admin/events", summary="The tail of the event stream (admin)")
async def event_stream(
    session: Annotated[AsyncSession, Depends(get_session)],
    _actor: AdminDep,
    limit: int = 50,
) -> dict[str, object]:
    rows = await events.recent(session, limit=limit)
    return {
        "total": await events.stream_size(session),
        "by_verb": await events.count_by_verb(session),
        "recent": [
            {
                "id": e.id,
                "verb": e.verb,
                "object_type": e.object_type,
                "object_id": str(e.object_id) if e.object_id else None,
                "payload": e.payload,
                "occurred_at": e.occurred_at.isoformat(),
            }
            for e in rows
        ],
    }
