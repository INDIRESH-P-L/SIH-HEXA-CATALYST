"""M4 · skill-gap models.

Every number here is produced by deterministic arithmetic in
``services/m4_gap_engine.py``. Nothing on these responses is model-generated,
and the API documentation says so.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

GapBandName = Literal["CRITICAL", "SIGNIFICANT", "EMERGING", "MET", "STRENGTH"]
HorizonName = Literal["current_role", "next_role"]


class GapDerivation(BaseModel):
    """Every multiplier behind a priority, so the arithmetic can be checked."""

    expected: int
    current: int
    difference: int
    criticality: float
    confidence: float
    uncertainty_multiplier: float = Field(
        description="2 - confidence. Unmeasured competencies are amplified."
    )
    horizon: str
    horizon_multiplier: float
    stale: bool
    priority: float
    formula: str


class GapRead(BaseModel):
    """One competency gap, with its derivation."""

    competency_id: uuid.UUID
    competency_code: str
    competency_name: str
    cluster: str
    required_level: int = Field(ge=0, le=4)
    current_level: int = Field(ge=0, le=4)
    gap: int = Field(ge=0, le=4, description="max(0, expected - current)")
    band: GapBandName
    priority: float = Field(
        description="(expected - current) x criticality x (2 - confidence) x horizon"
    )
    criticality: float = Field(ge=1.0, le=3.0)
    horizon: HorizonName
    confidence: float = Field(ge=0.0, le=1.0)
    frac_current: str
    frac_required: str
    stale: bool = Field(description="Evidence has aged past its decay class.")
    source_type: str | None = None
    assessed_at: datetime | None = None
    derivation: GapDerivation | None = None


class GapSummaryRead(BaseModel):
    """Counts per band, and the worst three gaps."""

    total_competencies: int
    critical: int
    significant: int
    emerging: int
    met: int
    strength: int
    open_gaps: int
    top_gaps: list[GapRead]
    average_current_level: float
    average_required_level: float
    stale_count: int
    unassessed_count: int


class GapListResponse(BaseModel):
    job_role_code: str | None = None
    job_role_title: str | None = None
    framework_version: str | None = None
    method: str = Field(
        default="deterministic",
        description=(
            "Rule-based arithmetic, not machine learning. "
            "priority = (expected - current) x criticality x (2 - confidence) x horizon."
        ),
    )
    scale: str = Field(
        default="FRAC 4-point: 1 Awareness, 2 Application, 3 Leveraging for decisions, 4 SME",
    )
    gaps: list[GapRead]
    summary: GapSummaryRead
    reassessment_candidates: list[str] = Field(
        default_factory=list,
        description="Competency codes whose evidence is stale or missing.",
    )


class ActivityRead(BaseModel):
    """A concrete action a role performs."""

    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    sequence: int
    competency_codes: list[str] = Field(default_factory=list)
