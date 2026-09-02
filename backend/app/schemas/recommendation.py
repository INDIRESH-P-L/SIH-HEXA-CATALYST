"""M5 · recommendation models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.catalogue import CourseRead


class PathwayStepRead(BaseModel):
    """Where this offering lands on the officer's calendar."""

    order: int
    starts_on: date
    ends_on: date
    months_required: float
    anchored: bool = Field(
        description="True when a dated academy session fixed the placement."
    )


class ScoreBreakdown(BaseModel):
    """Every term of the ranking formula, so the score can be audited on screen.

    final = 0.30·gap_priority + 0.20·semantic_similarity + 0.15·level_fit
          + 0.10·prerequisites_met + 0.10·effort_fit
          + 0.08·department_priority + 0.07·recency_language
    """

    gap_priority: float = Field(description="This gap's priority over the largest, 0-1.")
    semantic_similarity: float = Field(
        description="Cosine similarity between the competency and the course, 0-1."
    )
    level_fit: float = Field(
        description="How close the course level is to current_level + 1, 0-1."
    )
    prerequisites_met: float = Field(description="1.0 when every prerequisite is met.")
    effort_fit: float = Field(
        description="Whether the hours fit a serving officer's monthly budget."
    )
    department_priority: float = Field(
        description="Raised for competencies the department is pushing."
    )
    recency_language: float = Field(
        description="Freshness of the catalogue record and language match."
    )
    weights: dict[str, float]
    final_score: float

    # Stage 1 provenance.
    fusion_score: float | None = None
    retrievers: list[str] | None = Field(
        default=None, description="Which retrievers surfaced this candidate."
    )
    fusion: str | None = Field(default=None, description="How their rankings were combined.")

    # Stage 3 placement.
    sequence: PathwayStepRead | None = None

    # The gap this was recommended against, with its own derivation.
    gap_derivation: dict[str, Any] | None = None


class RecommendationRead(BaseModel):
    id: uuid.UUID
    batch_id: uuid.UUID
    rank: int
    score: float
    course: CourseRead
    competency_id: uuid.UUID | None = None
    competency_code: str | None = None
    competency_name: str | None = None
    current_level: int | None = None
    required_level: int | None = None
    gap_band: str | None = None
    explanation: str | None = None
    explanation_source: str = Field(
        default="template",
        description="'ai' when written by the language model, 'template' on fallback.",
    )
    breakdown: ScoreBreakdown
    created_at: datetime | None = None


class RecommendationBatch(BaseModel):
    batch_id: uuid.UUID
    generated_at: datetime
    count: int
    ai_explanations: int = Field(
        description="How many explanations the language model wrote."
    )
    llm_available: bool
    recommendations: list[RecommendationRead]
    method: str = Field(
        default="retrieve -> rank -> sequence",
        description=(
            "Three stages. Retrieval is semantic and lexical; ranking and "
            "sequencing are deterministic. The model writes only the "
            "explanatory sentence, after the order is fixed."
        ),
    )


class GenerateRequest(BaseModel):
    limit: int = Field(default=5, ge=1, le=10)
    max_per_competency: int = Field(default=2, ge=1, le=5)
    monthly_hours: int = Field(
        default=8,
        ge=1,
        le=160,
        description="Study hours a serving officer can realistically find each month.",
    )
    explain: bool = Field(
        default=True, description="Ask the language model for explanations."
    )


class RecommendationContext(BaseModel):
    """GET /recommendations/{id}/breakdown.

    Returns the exact anonymised JSON that was sent to the model, alongside the
    score terms. This is the panel that answers the privacy question.
    """

    recommendation_id: uuid.UUID
    rank: int
    score: float
    breakdown: ScoreBreakdown
    ai_context_sent: dict[str, Any] = Field(
        description="Whitelisted, anonymised context. Contains no personal data."
    )
    context_note: str = Field(
        default=(
            "This is the complete payload sent to the language model. It carries "
            "no name, no email, no employee code and no identifier."
        )
    )
    explanation: str | None = None
    explanation_source: str
    model: str | None = None
