"""M1 · profile endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.errors import NotFoundError
from app.core.security import CurrentUser, CurrentUserDep, require_role
from app.models.ai import ActivityLog
from app.models.user import Profile
from app.schemas.profile import JobRoleRead, ProfileRead, ProfileUpdate

router = APIRouter(prefix="/profiles", tags=["M1 · identity"])


def _to_read(profile: Profile) -> ProfileRead:
    return ProfileRead(
        id=profile.id,
        full_name=profile.full_name,
        employee_code=profile.employee_code,
        designation=profile.designation,
        department=profile.department,
        station=profile.station,
        cadre=profile.cadre,
        years_experience=profile.years_experience,
        education=profile.education,
        job_role=(
            JobRoleRead.model_validate(profile.job_role) if profile.job_role else None
        ),
        initial_assessment_completed=profile.initial_assessment_completed,
        created_at=profile.created_at,
    )


@router.patch("/me", response_model=ProfileRead, summary="Update your own profile")
async def update_me(
    payload: ProfileUpdate,
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProfileRead:
    profile = await session.get(Profile, user.id)
    if profile is None:
        raise NotFoundError("Profile not found.")

    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in changes.items():
        setattr(profile, field, value)
    if changes:
        profile.updated_at = func.now()
        session.add(
            ActivityLog(
                user_id=user.id,
                action="profile.update",
                entity="profile",
                entity_id=user.id,
                extra={"fields": sorted(changes)},
            )
        )

    await session.commit()
    refreshed = await session.get(Profile, user.id)
    assert refreshed is not None
    return _to_read(refreshed)


@router.get(
    "/{user_id}",
    response_model=ProfileRead,
    summary="Read another officer's profile (trainer or admin)",
)
async def get_profile(
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _actor: Annotated[CurrentUser, Depends(require_role("trainer", "admin"))],
) -> ProfileRead:
    profile = await session.get(Profile, user_id)
    if profile is None:
        raise NotFoundError("Profile not found.")
    return _to_read(profile)


@router.post(
    "/{user_id}/unblock",
    summary="Unblock an officer's account (admin only)",
)
async def unblock_user(
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _actor: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> dict[str, str]:
    profile = await session.get(Profile, user_id)
    if profile is None:
        raise NotFoundError("Profile not found.")
    
    profile.blocked_until = None
    session.add(ActivityLog(
        user_id=_actor.id,
        action="profile.unblocked",
        entity="profile",
        entity_id=user_id,
        extra={"reason": "Admin manually unblocked"},
    ))
    await session.commit()
    return {"status": "success", "message": "Account has been unblocked"}

@router.get(
    "/all/blocked",
    summary="List all currently blocked accounts (admin only)",
)
async def get_blocked_accounts(
    session: Annotated[AsyncSession, Depends(get_session)],
    _actor: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> list[dict]:
    from sqlalchemy import select
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    stmt = select(Profile).where(Profile.blocked_until > now)
    result = await session.execute(stmt)
    profiles = result.scalars().all()
    
    return [
        {
            "id": str(p.id),
            "full_name": p.full_name,
            "email": p.employee_code,
            "blocked_until": p.blocked_until.isoformat() if p.blocked_until else None,
        }
        for p in profiles
    ]

