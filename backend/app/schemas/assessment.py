"""M3 · assessment models, including the closed-loop submit payload."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.question import QuizQuestion

AssessmentStatusName = Literal["IN_PROGRESS", "SUBMITTED", "ABANDONED"]


class CreateAssessmentRequest(BaseModel):
    competency_id: uuid.UUID
    mode: Literal["proctored", "practice"] = Field(
        default="practice",
        description=(
            "Proctored attempts write evidence at 0.90 confidence and count "
            "towards workforce dashboards. Practice writes 0.50 and does not."
        ),
    )
    material_id: uuid.UUID | None = Field(
        default=None,
        description="Restrict the question bank to one uploaded document.",
    )
    count: int = Field(default=10, ge=1, le=50)


class AssessmentRead(BaseModel):
    """GET /assessments/{id} — questions WITHOUT the answer key."""

    id: uuid.UUID
    status: AssessmentStatusName
    competency_id: uuid.UUID | None = None
    competency_code: str | None = None
    competency_name: str | None = None
    material_id: uuid.UUID | None = None
    total_questions: int
    answered_count: int
    started_at: datetime | None = None
    questions: list[QuizQuestion]


class AnswerRequest(BaseModel):
    question_id: uuid.UUID
    selected_index: int = Field(ge=0, le=3)


class AnswerResponse(BaseModel):
    """Deliberately does not reveal whether the answer was right.

    Correctness is disclosed at submit time, not per question, so the officer
    cannot probe the key one option at a time.
    """

    assessment_id: uuid.UUID
    question_id: uuid.UUID
    selected_index: int
    answered_count: int
    total_questions: int


class GapSnapshot(BaseModel):
    gap: int
    band: str
    frac: str | None = None


class CompetencyRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    code: str
    name: str


class NewRecommendationRef(BaseModel):
    rank: int
    course_id: uuid.UUID
    title: str
    provider: str
    source: str
    proficiency_level: int
    duration_hours: int
    explanation: str | None = None
    explanation_source: str = "template"


class ScoringBreakdown(BaseModel):
    """The arithmetic behind the score, reproducible from stored responses."""

    weighted_score: float
    raw_score: float
    numerator: int
    denominator: int
    attempted: int
    correct: int
    total_items: int
    weights: dict[str, int]
    per_difficulty: dict[str, dict[str, int]]
    formula: str


class SubmitResponse(BaseModel):
    """The payload the whole demo is built around.

    Steps 1-6 of the closed loop run in one transaction: score, read the level
    before, compute the level after, write the evidence row, recompute the gap,
    regenerate recommendations. The AI feedback is step 7, best-effort, and
    cannot fail the request.
    """

    assessment_id: uuid.UUID
    score: float = Field(description="Difficulty-weighted percentage.")
    raw_score: float = Field(description="Unweighted percentage, for comparison.")
    breakdown: ScoringBreakdown
    mode: str
    confidence: float = Field(description="Confidence of the evidence row written.")
    correct_count: int
    attempted: int
    total_questions: int
    competency: CompetencyRef
    level_before: int
    level_after: int
    level_changed: bool
    frac_before: str
    frac_after: str
    gap_before: GapSnapshot
    gap_after: GapSnapshot
    priority_before: float
    priority_after: float
    weak_topics: list[str]
    strong_topics: list[str]
    revisit: bool = Field(
        description="Set when the score was below the pass mark. Levels never fall."
    )
    ai_feedback: str
    feedback_source: str = Field(
        description="'ai' when the language model wrote it, 'template' on fallback."
    )
    new_recommendations: list[NewRecommendationRef]
    evidence_id: uuid.UUID
    scoring_note: str = Field(
        default=(
            "Score, level change and weak topics are computed deterministically. "
            "The language model writes only the prose feedback."
        )
    )


class AssessmentHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: AssessmentStatusName
    competency_code: str | None = None
    competency_name: str | None = None
    total_questions: int
    correct_count: int | None = None
    score: float | None = None
    level_before: int | None = None
    level_after: int | None = None
    started_at: datetime | None = None
    submitted_at: datetime | None = None
