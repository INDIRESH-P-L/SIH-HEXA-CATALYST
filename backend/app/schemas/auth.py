"""M1 · authentication request and response models."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.schemas.profile import ProfileRead


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    job_role_code: str = Field(
        default="STAT_OFFICER",
        description="Job role code, e.g. STAT_OFFICER. See GET /job-roles.",
    )
    employee_code: str | None = Field(default=None, max_length=64)
    designation: str | None = Field(default=None, max_length=120)
    station: str | None = Field(default=None, max_length=120)
    years_experience: int = Field(default=0, ge=0, le=60)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Seconds until the token expires.")
    user: "MeResponse"


class MeResponse(BaseModel):
    """GET /auth/me — identity, roles and profile in one call."""

    id: uuid.UUID
    email: str | None
    roles: list[str]
    profile: ProfileRead
    auth_mode: str = Field(
        description="Which auth seam issued this session: local or supabase."
    )
    onboarded: bool = Field(
        default=True,
        description=(
            "Whether this officer has any competency evidence on file. False "
            "means the onboarding wizard has never been completed. Derived "
            "from the ledger, not from a client-side flag, so it holds across "
            "devices."
        ),
    )


TokenResponse.model_rebuild()
