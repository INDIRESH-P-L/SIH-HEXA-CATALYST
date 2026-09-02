"""M1 · profile models."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobRoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: str
    cadre: str
    description: str | None = None


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    employee_code: str | None = None
    designation: str | None = None
    department: str | None = None
    station: str | None = None
    cadre: str | None = None
    years_experience: int | None = None
    education: str | None = None
    job_role: JobRoleRead | None = None
    initial_assessment_completed: bool = False
    created_at: datetime | None = None


class ProfileUpdate(BaseModel):
    """PATCH /profiles/me. Every field optional; omitted fields are untouched.

    job_role_id is deliberately absent: an officer does not reassign their own
    post. Changing it is an administrative action.
    """

    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    designation: str | None = Field(default=None, max_length=120)
    station: str | None = Field(default=None, max_length=120)
    years_experience: int | None = Field(default=None, ge=0, le=60)
    education: str | None = Field(default=None, max_length=240)
