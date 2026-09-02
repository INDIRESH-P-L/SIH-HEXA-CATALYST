"""M2 · competency framework models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Cluster = Literal["STATISTICAL", "TECHNICAL", "DIGITAL_GOVERNANCE", "BEHAVIOURAL"]


class CompetencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    cluster: Cluster
    description: str
    frac_type: str | None = None
    kind: str | None = Field(default=None, description="knowledge | skill | attribute")
    decay: str | None = Field(
        default=None,
        description=(
            "How fast evidence goes stale: tools 18 months, regulatory 12, "
            "methodology 36, behavioural never."
        ),
    )


class RequirementRead(BaseModel):
    """One row of a role's requirement matrix."""

    competency: CompetencyRead
    required_level: int = Field(ge=1, le=4)
    required_frac: str = Field(description="FRAC label for the required level.")
    criticality: float = Field(
        ge=1.0, le=3.0, description="Multiplier applied to the gap to set priority."
    )
    horizon: str = Field(
        default="current_role", description="current_role | next_role"
    )


class JobRoleRequirements(BaseModel):
    job_role_id: uuid.UUID
    job_role_code: str
    job_role_title: str
    requirements: list[RequirementRead]


class MyCompetencyRead(BaseModel):
    """An officer's standing in one competency."""

    competency: CompetencyRead
    current_level: int = Field(ge=0, le=4)
    current_frac: str
    required_level: int | None = Field(default=None, ge=1, le=4)
    required_frac: str | None = None
    confidence: float | None = None
    source_type: str | None = None
    assessed_at: datetime | None = None


class DeclareRequest(BaseModel):
    """POST /competencies/me/declare — a self-declared baseline.

    Recorded with confidence 0.25. Self-declaration is the weakest evidence the
    ledger accepts; an assessment result carries 0.90.
    """

    competency_id: uuid.UUID
    level: int = Field(ge=0, le=4)
    note: str | None = Field(default=None, max_length=500)


class DeclareBatchRequest(BaseModel):
    declarations: list[DeclareRequest] = Field(min_length=1, max_length=50)


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    competency_id: uuid.UUID
    level: int
    score: float | None = None
    source_type: str
    source_ref: uuid.UUID | None = None
    confidence: float
    note: str | None = None
    created_at: datetime
