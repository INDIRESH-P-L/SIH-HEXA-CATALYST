"""M6 · catalogue endpoints.

The catalogue behind these endpoints is a mock service conforming to a
documented interface. This prototype does not have access to the official iGOT
Karmayogi or NSSTA APIs; production deployment requires authorised credentials
from the Capacity Building Commission (iGOT) and NSSTA.

``GET /catalogue/provider-info`` reports exactly that, and the interface renders
it as a visible badge so the claim can be checked rather than trusted.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.errors import ConflictError, NotFoundError, UpstreamUnavailable
from app.core.logging import get_logger
from app.core.security import CurrentUser, CurrentUserDep, require_role
from app.models.ai import ActivityLog
from app.models.course import Course, Enrollment
from app.schemas.catalogue import (
    CourseRead,
    EnrollmentRead,
    NominateRequest,
    ProviderInfoResponse,
    SyncResponse,
)
from app.services.m6_catalogue.mock_provider import MockProvider
from app.services.m6_catalogue.provider import get_catalogue_provider
from app.services.m6_catalogue.sync import mirror_stats, sync_catalogue

log = get_logger(__name__)
router = APIRouter(prefix="/catalogue", tags=["M6 · catalogue"])


@router.get(
    "/provider-info",
    response_model=ProviderInfoResponse,
    summary="Which catalogue is behind this data, and is it a mock",
)
async def provider_info(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: CurrentUserDep,
) -> ProviderInfoResponse:
    provider = get_catalogue_provider()
    info = provider.info()
    stats = await mirror_stats(session)
    reachable = await provider.health()
    return ProviderInfoResponse(
        provider=info.provider,
        is_mock=info.is_mock,
        description=info.description,
        base_url=info.base_url,
        record_count=stats["total"],
        embedded_count=stats["embedded"],
        reachable=reachable,
        circuit_state=(
            MockProvider.breaker_state() if isinstance(provider, MockProvider) else None
        ),
    )


@router.get(
    "/courses", response_model=list[CourseRead], summary="Browse the catalogue mirror"
)
async def list_courses(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: CurrentUserDep,
    competency: Annotated[str | None, Query(description="Competency code.")] = None,
    level: Annotated[int | None, Query(ge=1, le=5)] = None,
    source: Annotated[str | None, Query(description="IGOT or NSSTA.")] = None,
    q: Annotated[str | None, Query(description="Free-text search.")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[CourseRead]:
    """Served from the local mirror, not from the catalogue service.

    The mirror is what makes browsing work when the upstream service is down,
    and it is where the embeddings live.
    """
    stmt = select(Course).where(Course.status == "ACTIVE")
    if competency:
        stmt = stmt.where(Course.competency_code == competency.upper())
    if level is not None:
        stmt = stmt.where(Course.proficiency_level == level)
    if source:
        stmt = stmt.where(Course.source == source.upper())
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(Course.title.ilike(pattern), Course.description.ilike(pattern))
        )
    stmt = stmt.order_by(Course.source, Course.proficiency_level, Course.title).limit(limit)

    rows = (await session.execute(stmt)).scalars().all()
    return [CourseRead.model_validate(c) for c in rows]


@router.get(
    "/my-enrollments",
    response_model=list[EnrollmentRead],
    summary="Your enrolments and nomination requests",
)
async def my_enrollments(
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[EnrollmentRead]:
    rows = (
        await session.execute(
            select(Enrollment)
            .where(Enrollment.user_id == user.id)
            .order_by(Enrollment.created_at.desc())
        )
    ).scalars().all()
    return [
        EnrollmentRead(
            id=e.id,
            course_id=e.course_id,
            status=e.status,  # type: ignore[arg-type]
            external_ref=e.external_ref,
            enrolled_at=e.enrolled_at,
            completed_at=e.completed_at,
            created_at=e.created_at,
            course=CourseRead.model_validate(e.course) if e.course else None,
        )
        for e in rows
    ]


@router.get("/courses/{course_id}", response_model=CourseRead, summary="One course")
async def get_course(
    course_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: CurrentUserDep,
) -> CourseRead:
    course = await session.get(Course, course_id)
    if course is None:
        raise NotFoundError("No such course.")
    return CourseRead.model_validate(course)


@router.post(
    "/courses/{course_id}/enroll",
    response_model=EnrollmentRead,
    summary="Self-enrol on an iGOT course",
)
async def enroll(
    course_id: uuid.UUID,
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EnrollmentRead:
    """The iGOT path: self-enrolment, effective immediately.

    ``user_ref`` sent upstream is the opaque account id, never a name or an
    employee code.
    """
    course = await session.get(Course, course_id)
    if course is None:
        raise NotFoundError("No such course.")
    if course.source != "IGOT":
        raise ConflictError(
            "NSSTA programmes are nominated for, not self-enrolled. "
            "Use POST /catalogue/programmes/{id}/nominate."
        )

    existing = await session.scalar(
        select(Enrollment)
        .where(Enrollment.user_id == user.id)
        .where(Enrollment.course_id == course_id)
    )
    if existing is not None and existing.status in ("ENROLLED", "IN_PROGRESS", "COMPLETED"):
        raise ConflictError("You are already enrolled on this course.")

    provider = get_catalogue_provider()
    external_ref: str | None = None
    note: str | None = None
    try:
        result = await provider.enroll(str(user.id), course.external_id)
        external_ref = result.external_ref
    except UpstreamUnavailable as exc:
        # Record the intent locally so the officer does not lose it, and say
        # plainly that upstream confirmation is outstanding.
        note = f"Recorded locally; the catalogue service did not confirm ({exc.message})."
        log.warning("enrol upstream failed for %s: %s", course.external_id, exc.message)

    now = datetime.now(tz=timezone.utc)
    if existing is None:
        enrollment = Enrollment(
            user_id=user.id,
            course_id=course_id,
            status="ENROLLED",
            external_ref=external_ref,
            enrolled_at=now,
        )
        session.add(enrollment)
    else:
        existing.status = "ENROLLED"
        existing.external_ref = external_ref
        existing.enrolled_at = now
        enrollment = existing

    session.add(
        ActivityLog(
            user_id=user.id,
            action="catalogue.enroll",
            entity="enrollments",
            entity_id=course_id,
            extra={"external_id": course.external_id, "external_ref": external_ref},
        )
    )
    await session.commit()
    await session.refresh(enrollment)

    return EnrollmentRead(
        id=enrollment.id,
        course_id=enrollment.course_id,
        status=enrollment.status,  # type: ignore[arg-type]
        external_ref=enrollment.external_ref,
        enrolled_at=enrollment.enrolled_at,
        completed_at=enrollment.completed_at,
        created_at=enrollment.created_at,
        course=CourseRead.model_validate(course),
        note=note,
    )


@router.post(
    "/programmes/{course_id}/nominate",
    response_model=EnrollmentRead,
    summary="Request nomination for an NSSTA programme",
)
async def nominate(
    course_id: uuid.UUID,
    payload: NominateRequest,
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EnrollmentRead:
    """The NSSTA path: a request, not an enrolment.

    An officer requests, a controlling authority nominates, and the academy
    confirms against available seats. Only the first step is modelled here, and
    the status returned says so: NOMINATION_REQUESTED.
    """
    course = await session.get(Course, course_id)
    if course is None:
        raise NotFoundError("No such programme.")
    if course.source != "NSSTA":
        raise ConflictError(
            "iGOT courses are self-enrolled. "
            "Use POST /catalogue/courses/{id}/enroll."
        )

    existing = await session.scalar(
        select(Enrollment)
        .where(Enrollment.user_id == user.id)
        .where(Enrollment.course_id == course_id)
    )
    if existing is not None and existing.status == "NOMINATION_REQUESTED":
        raise ConflictError("A nomination request is already pending for you.")

    provider = get_catalogue_provider()
    external_ref: str | None = None
    note = (
        "Nomination requested. Approval rests with the controlling authority and "
        "confirmation with the academy; neither step is implemented in this "
        "prototype."
    )
    try:
        result = await provider.nominate(
            str(user.id), course.external_id, payload.justification
        )
        external_ref = result.external_ref
    except UpstreamUnavailable as exc:
        note = f"Recorded locally; the catalogue service did not confirm ({exc.message})."
        log.warning("nominate upstream failed for %s: %s", course.external_id, exc.message)

    if existing is None:
        enrollment = Enrollment(
            user_id=user.id,
            course_id=course_id,
            status="NOMINATION_REQUESTED",
            external_ref=external_ref,
        )
        session.add(enrollment)
    else:
        existing.status = "NOMINATION_REQUESTED"
        existing.external_ref = external_ref
        enrollment = existing

    session.add(
        ActivityLog(
            user_id=user.id,
            action="catalogue.nominate",
            entity="enrollments",
            entity_id=course_id,
            extra={"external_id": course.external_id, "external_ref": external_ref},
        )
    )
    await session.commit()
    await session.refresh(enrollment)

    return EnrollmentRead(
        id=enrollment.id,
        course_id=enrollment.course_id,
        status=enrollment.status,  # type: ignore[arg-type]
        external_ref=enrollment.external_ref,
        enrolled_at=enrollment.enrolled_at,
        completed_at=enrollment.completed_at,
        created_at=enrollment.created_at,
        course=CourseRead.model_validate(course),
        note=note,
    )


@router.post(
    "/sync",
    response_model=SyncResponse,
    summary="Re-pull and re-embed the catalogue (admin)",
)
async def sync(
    session: Annotated[AsyncSession, Depends(get_session)],
    actor: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> SyncResponse:
    provider = get_catalogue_provider()
    result = await sync_catalogue(session, provider)
    session.add(
        ActivityLog(
            user_id=actor.id,
            action="catalogue.sync",
            entity="courses",
            extra=result.as_dict(),
        )
    )
    await session.commit()
    return SyncResponse(**result.as_dict())  # type: ignore[arg-type]


@router.get(
    "/stats", response_model=dict, summary="Mirror counts by source and competency"
)
async def stats(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: CurrentUserDep,
) -> dict:
    by_source = (
        await session.execute(
            select(Course.source, func.count()).group_by(Course.source)
        )
    ).all()
    by_competency = (
        await session.execute(
            select(Course.competency_code, func.count())
            .group_by(Course.competency_code)
            .order_by(Course.competency_code)
        )
    ).all()
    mirror = await mirror_stats(session)
    return {
        "total": mirror["total"],
        "embedded": mirror["embedded"],
        "by_source": {str(s): int(c) for s, c in by_source},
        "by_competency": {str(k): int(c) for k, c in by_competency},
    }
