"""M8 · question and validation models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Difficulty = Literal["easy", "medium", "hard"]
QuestionStatusName = Literal["DRAFT", "APPROVED", "REJECTED"]


class CheckResult(BaseModel):
    """Outcome of one deterministic validation check."""

    passed: bool
    detail: str | None = None


class ValidationReport(BaseModel):
    """Per-question verdict from the validation gate. No model involved."""

    passed: bool
    failed_checks: list[str] = Field(default_factory=list)
    checks: dict[str, CheckResult]


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    material_id: uuid.UUID | None = None
    competency_id: uuid.UUID | None = None
    question_text: str
    options: list[str]
    correct_index: int = Field(ge=0, le=3)
    explanation: str
    difficulty: Difficulty
    topic: str | None = None
    status: QuestionStatusName
    validation: ValidationReport | None = None
    source_page: int | None = None
    created_at: datetime | None = None


class QuizQuestion(BaseModel):
    """A question as served during a quiz.

    correct_index and explanation are deliberately absent. The client is never
    sent the key while the assessment is open.
    """

    id: uuid.UUID
    position: int
    question_text: str
    options: list[str]
    difficulty: Difficulty
    topic: str | None = None
    source_page: int | None = None
    selected_index: int | None = None


class QuestionUpdate(BaseModel):
    """PATCH /questions/{id} — trainer review."""

    status: QuestionStatusName | None = None
    question_text: str | None = Field(default=None, min_length=15, max_length=300)
    options: list[str] | None = Field(default=None, min_length=4, max_length=4)
    correct_index: int | None = Field(default=None, ge=0, le=3)
    explanation: str | None = Field(default=None, min_length=20)
    difficulty: Difficulty | None = None
    topic: str | None = None


class GenerationSummary(BaseModel):
    """The validation report a trainer sees after a generation run."""

    material_id: uuid.UUID
    requested: int
    generated: int
    passed: int
    rejected: int
    retried: int
    chunks_used: int
    llm_available: bool
    model: str | None = None
    rejection_reasons: dict[str, int] = Field(
        default_factory=dict, description="Check name -> how many items it rejected."
    )
    check_pass_counts: dict[str, int] = Field(default_factory=dict)
    questions: list[QuestionRead] = Field(default_factory=list)
    rejected_questions: list[QuestionRead] = Field(default_factory=list)
    note: str | None = None
