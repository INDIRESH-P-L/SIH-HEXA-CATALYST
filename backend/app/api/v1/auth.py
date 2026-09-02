"""M1 · authentication endpoints.

Registration and login are proxied to whichever auth backend AUTH_MODE selects.
Everything downstream of a token — verification, roles, RBAC — is identical in
both modes.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.errors import AuthError, ConflictError
from app.core.logging import get_logger
from app.core.security import CurrentUserDep, load_roles
from app.models.ai import ActivityLog
from app.models.user import Profile, UserRole
from app.schemas.auth import LoginRequest, MeResponse, RegisterRequest, TokenResponse
from app.schemas.profile import JobRoleRead, ProfileRead
from app.services.m1_identity import get_auth_backend
from app.services.m2_framework import get_job_role_by_code, has_evidence_on_file

log = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["M1 · identity"])


def _profile_payload(profile: Profile) -> ProfileRead:
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
        created_at=profile.created_at,
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account and sign in",
)
async def register(
    payload: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    """Create an identity, a profile and a default role.

    Under AUTH_MODE=local all three writes share one transaction. Under
    AUTH_MODE=supabase the identity is created remotely first; if the local
    writes then fail, the transaction rolls back and the orphaned identity is
    reported rather than hidden.
    """
    backend = get_auth_backend()
    job_role = await get_job_role_by_code(session, payload.job_role_code)

    auth_user = await backend.register(
        session=session, email=str(payload.email), password=payload.password
    )

    existing = await session.get(Profile, auth_user.id)
    if existing is not None:
        raise ConflictError("A profile already exists for that account.")

    profile = Profile(
        id=auth_user.id,
        full_name=payload.full_name,
        employee_code=payload.employee_code,
        designation=payload.designation or job_role.title,
        station=payload.station,
        job_role_id=job_role.id,
        cadre=job_role.cadre,
        years_experience=payload.years_experience,
    )
    session.add(profile)

    await session.execute(
        pg_insert(UserRole)
        .values(user_id=auth_user.id, role="employee")
        .on_conflict_do_nothing(index_elements=[UserRole.user_id, UserRole.role])
    )
    session.add(
        ActivityLog(
            user_id=auth_user.id,
            action="auth.register",
            entity="profile",
            entity_id=auth_user.id,
            extra={"job_role_code": job_role.code, "auth_mode": settings.AUTH_MODE},
        )
    )

    session_dto = await backend.login(
        session=session, email=str(payload.email), password=payload.password
    )
    await session.commit()

    refreshed = await session.get(Profile, auth_user.id)
    assert refreshed is not None
    roles = await load_roles(session, auth_user.id)

    return TokenResponse(
        access_token=session_dto.access_token,
        expires_in=session_dto.expires_in,
        user=MeResponse(
            id=auth_user.id,
            email=auth_user.email,
            roles=sorted(roles),
            profile=_profile_payload(refreshed),
            auth_mode=settings.AUTH_MODE,
            # A brand-new account has an empty ledger, which is precisely what
            # sends it to the onboarding wizard.
            onboarded=False,
        ),
    )


@router.post("/login", response_model=TokenResponse, summary="Sign in")
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    backend = get_auth_backend()
    session_dto = await backend.login(
        session=session, email=str(payload.email), password=payload.password
    )

    profile = await session.get(Profile, session_dto.user_id)
    if profile is None:
        raise AuthError("That account has no profile in this deployment.")

    roles = await load_roles(session, session_dto.user_id)
    onboarded = await has_evidence_on_file(session, session_dto.user_id)
    session.add(
        ActivityLog(
            user_id=session_dto.user_id,
            action="auth.login",
            entity="profile",
            entity_id=session_dto.user_id,
            extra={"auth_mode": settings.AUTH_MODE},
        )
    )
    await session.commit()

    return TokenResponse(
        access_token=session_dto.access_token,
        expires_in=session_dto.expires_in,
        user=MeResponse(
            id=session_dto.user_id,
            email=session_dto.email,
            roles=sorted(roles) or ["employee"],
            profile=_profile_payload(profile),
            auth_mode=settings.AUTH_MODE,
            onboarded=onboarded,
        ),
    )


@router.get("/me", response_model=MeResponse, summary="The signed-in officer")
async def me(
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        roles=sorted(user.roles),
        profile=_profile_payload(user.profile),
        auth_mode=settings.AUTH_MODE,
        onboarded=await has_evidence_on_file(session, user.id),
    )
