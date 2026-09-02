"""M6 · catalogue models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CatalogueSourceName = Literal["IGOT", "NSSTA"]
LearningFormatName = Literal["SELF_PACED", "CLASSROOM", "BLENDED", "VIRTUAL_LAB"]
EnrollmentStatusName = Literal[
    "RECOMMENDED", "ENROLLED", "NOMINATION_REQUESTED", "IN_PROGRESS", "COMPLETED"
]


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: str
    source: CatalogueSourceName
    title: str
    provider: str
    competency_code: str
    proficiency_level: int = Field(ge=1, le=4)
    duration_hours: int
    description: str
    prerequisites: list[str] = Field(default_factory=list)
    learning_format: LearningFormatName
    course_url: str | None = None
    status: str = "ACTIVE"
    session_start: date | None = None
    seats: int | None = None
    synced_at: datetime | None = None


class ProviderInfoResponse(BaseModel):
    """GET /catalogue/provider-info.

    Rendered by the frontend as a visible badge on catalogue data so a judge
    can verify the claim rather than take it on trust.
    """

    provider: str
    is_mock: bool
    description: str
    base_url: str | None = None
    record_count: int | None = None
    embedded_count: int | None = None
    reachable: bool | None = None
    circuit_state: str | None = None


class EnrollRequest(BaseModel):
    """iGOT courses are self-enrolled, so no justification is required."""


class NominateRequest(BaseModel):
    """NSSTA programmes are nominated for, not self-enrolled."""

    justification: str = Field(
        default="",
        max_length=1000,
        description="Reason submitted to the controlling authority.",
    )


class EnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    status: EnrollmentStatusName
    external_ref: str | None = None
    enrolled_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    course: CourseRead | None = None
    note: str | None = None


class SyncResponse(BaseModel):
    fetched: int
    upserted: int
    embedded: int
    igot: int
    nssta: int
    provider: str
    is_mock: bool
