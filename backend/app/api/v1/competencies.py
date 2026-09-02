"""M2 · competency framework endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.errors import NotFoundError
from app.core.security import CurrentUserDep
from app.models.ai import ActivityLog
from app.schemas.competency import (
    CompetencyRead,
    DeclareBatchRequest,
    DeclareRequest,
    EvidenceRead,
    JobRoleRequirements,
    MyCompetencyRead,
    RequirementRead,
)
from app.schemas.profile import JobRoleRead
from app.services import m2_framework as framework
from app.services.m4_gap_engine import frac_label

router = APIRouter(tags=["M2 · competency framework"])


@router.get(
    "/competencies",
    response_model=list[CompetencyRead],
    summary="The competency framework",
)
async def list_competencies(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: CurrentUserDep,
    cluster: Annotated[str | None, Query(description="Filter by cluster.")] = None,
) -> list[CompetencyRead]:
    rows = await framework.list_competencies(session, cluster)
    return [CompetencyRead.model_validate(c) for c in rows]


@router.get(
    "/competencies/me",
    response_model=list[MyCompetencyRead],
    summary="Your competency standing against your role",
)
async def my_competencies(
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[MyCompetencyRead]:
    """Every competency in the framework, with your level and your requirement.

    Competencies you have no evidence for are still listed, at level 0. An
    unassessed requirement is information, not a blank row.
    """
    competencies = await framework.list_competencies(session)
    levels = await framework.load_current_levels(session, user.id)
    standing = {
        str(s.competency_id): s
        for s in await framework.load_competency_standing(session, user.id)
    }

    requirements: dict[str, RequirementRead] = {}
    if user.profile.job_role_id:
        for requirement, competency in await framework.load_requirements(
            session, user.profile.job_role_id
        ):
            requirements[str(competency.id)] = RequirementRead(
                competency=CompetencyRead.model_validate(competency),
                required_level=requirement.required_level,
                required_frac=frac_label(requirement.required_level),
                criticality=float(requirement.criticality),
            )

    out: list[MyCompetencyRead] = []
    for competency in competencies:
        key = str(competency.id)
        current = levels.get(key, 0)
        record = standing.get(key)
        requirement = requirements.get(key)
        out.append(
            MyCompetencyRead(
                competency=CompetencyRead.model_validate(competency),
                current_level=current,
                current_frac=frac_label(current),
                required_level=requirement.required_level if requirement else None,
                required_frac=requirement.required_frac if requirement else None,
                confidence=float(record.confidence) if record else None,
                source_type=record.source_type if record else None,
                assessed_at=record.assessed_at if record else None,
            )
        )
    return out


@router.get(
    "/competencies/{competency_id}",
    response_model=CompetencyRead,
    summary="One competency",
)
async def get_competency(
    competency_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: CurrentUserDep,
) -> CompetencyRead:
    return CompetencyRead.model_validate(
        await framework.get_competency(session, competency_id)
    )


@router.post(
    "/competencies/me/declare",
    response_model=list[EvidenceRead],
    summary="Declare your own baseline levels",
)
async def declare(
    payload: DeclareRequest | DeclareBatchRequest,
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[EvidenceRead]:
    """Record self-declared levels at confidence 0.25.

    Accepts one declaration or a batch. Nothing is overwritten: each call
    appends to the evidence ledger, and the most recent row is what counts.
    """
    declarations = (
        payload.declarations
        if isinstance(payload, DeclareBatchRequest)
        else [payload]
    )

    written = []
    for item in declarations:
        evidence = await framework.declare_baseline(
            session,
            user_id=user.id,
            competency_id=item.competency_id,
            level=item.level,
            note=item.note,
        )
        written.append(evidence)

    session.add(
        ActivityLog(
            user_id=user.id,
            action="competency.declare",
            entity="competency_evidence",
            extra={"count": len(written)},
        )
    )
    await session.commit()
    return [EvidenceRead.model_validate(e) for e in written]


@router.get("/job-roles", response_model=list[JobRoleRead], summary="Job roles")
async def list_job_roles(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: CurrentUserDep,
) -> list[JobRoleRead]:
    return [
        JobRoleRead.model_validate(r) for r in await framework.list_job_roles(session)
    ]


@router.get(
    "/job-roles/{job_role_id}/requirements",
    response_model=JobRoleRequirements,
    summary="A role's required levels and criticality",
)
async def job_role_requirements(
    job_role_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: CurrentUserDep,
) -> JobRoleRequirements:
    role = await framework.get_job_role(session, job_role_id)
    rows = await framework.load_requirements(session, job_role_id)
    if not rows:
        raise NotFoundError("That job role has no competency requirements defined.")

    return JobRoleRequirements(
        job_role_id=role.id,
        job_role_code=role.code,
        job_role_title=role.title,
        requirements=[
            RequirementRead(
                competency=CompetencyRead.model_validate(competency),
                required_level=requirement.required_level,
                required_frac=frac_label(requirement.required_level),
                criticality=float(requirement.criticality),
            )
            for requirement, competency in rows
        ],
    )
