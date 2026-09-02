"""M9 · analytics models. Deterministic SQL aggregates throughout."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class StatTile(BaseModel):
    """A single headline number."""

    label: str
    value: float
    unit: str | None = None
    delta: float | None = None


class ProgressPoint(BaseModel):
    """One point on the competency progress line.

    There is one point per evidence event, stamped with the moment that
    evidence was written — not bucketed by calendar day. Bucketing by day
    collapses a whole demonstration into a single point, because seeding, the
    assessment and everything after it happen within the same day.
    """

    at: datetime
    average_level: float
    competency_code: str | None = None
    level: int | None = None


class RadarPoint(BaseModel):
    """One axis of the competency radar."""

    competency_code: str
    competency_name: str
    current_level: int
    required_level: int


class MyAnalytics(BaseModel):
    """GET /analytics/me."""

    competencies_tracked: int
    average_current_level: float
    average_required_level: float
    gaps_open: int
    critical_gaps: int = 0
    stale_competencies: int = 0
    unassessed_competencies: int = 0
    learning_hours_completed: int
    courses_completed: int
    courses_in_progress: int
    assessments_taken: int
    levels_gained: int
    radar: list[RadarPoint]
    progress: list[ProgressPoint]
    tiles: list[StatTile]


class CompetencyGapFrequency(BaseModel):
    competency_code: str
    competency_name: str
    officers_with_gap: int
    average_gap: float
    average_current_level: float
    average_required_level: float
    dominant_band: str
    officers: int = 0
    suppressed: bool = Field(
        default=False,
        description="Withheld: fewer officers than the k-anonymity threshold.",
    )


class LevelDistributionBucket(BaseModel):
    level: int
    frac_label: str
    count: int


class MatrixCell(BaseModel):
    job_role_code: str
    job_role_title: str
    competency_code: str
    competency_name: str
    average_level: float
    required_level: int
    officers: int
    suppressed: bool = False


class CompetencyMatrix(BaseModel):
    """GET /analytics/admin/competency-matrix — heatmap data."""

    job_roles: list[str]
    competencies: list[str]
    cells: list[MatrixCell]
    k_anonymity_threshold: int = 5


class AdminOverview(BaseModel):
    """GET /analytics/admin/overview."""

    total_officers: int
    total_competencies: int
    total_courses: int
    total_assessments: int = Field(
        description="Proctored only. Practice attempts are excluded."
    )
    officers_with_critical_gap: int
    stale_evidence_rows: int = 0
    unassessed_requirements: int = 0
    events_recorded: int = 0
    band_counts: dict[str, int]
    level_distribution: list[LevelDistributionBucket]
    gap_frequency: list[CompetencyGapFrequency]
    tiles: list[StatTile]
    k_anonymity_threshold: int = 5
    note: str = Field(
        default=(
            "Deterministic aggregates. Cells covering fewer than five "
            "officers are suppressed, and no individual score appears in "
            "any workforce view. Practice attempts are excluded."
        )
    )


class TrainingEffectivenessRow(BaseModel):
    course_id: uuid.UUID
    course_title: str
    source: str
    competency_code: str
    completions: int
    average_level_before: float
    average_level_after: float
    average_delta: float
    comparison_delta: float | None = Field(
        default=None,
        description="Average change among officers who did not attend.",
    )
    net_delta: float | None = Field(
        default=None, description="average_delta minus comparison_delta."
    )
    suppressed: bool = False


class TrainingEffectiveness(BaseModel):
    """GET /analytics/admin/training-effectiveness."""

    rows: list[TrainingEffectivenessRow]
    k_anonymity_threshold: int = 5
    note: str = Field(
        default=(
            "Completion percentage answers whether officers attended. This "
            "answers whether it worked: the pre/post competency delta "
            "either side of a recorded completion, against officers who "
            "did not attend. That comparison group is not a randomised "
            "control; it is the honest available counterfactual."
        )
    )
