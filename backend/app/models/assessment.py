"""M3 · assessments and the answers given to them."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

ASSESSMENT_STATUS = Enum(
    "IN_PROGRESS", "SUBMITTED", "ABANDONED", name="assessment_status", create_type=False
)


class Assessment(Base):
    """One quiz attempt.

    ``level_before`` and ``level_after`` are written by the submit endpoint and
    are what the result screen animates between. Both are computed by rule, not
    by a model. ``feedback`` is the single LLM-written field and is best-effort:
    if the model is unavailable a templated string is stored instead.
    """

    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE")
    )
    competency_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id")
    )
    material_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("learning_materials.id")
    )
    status: Mapped[str] = mapped_column(ASSESSMENT_STATUS, default="IN_PROGRESS")
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_count: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    level_before: Mapped[int | None] = mapped_column(Integer)
    level_after: Mapped[int | None] = mapped_column(Integer)
    feedback: Mapped[str | None] = mapped_column(Text)
    #: Proctored attempts write evidence at 0.90; practice at 0.50, and
    #: stay out of administrator aggregates.
    mode: Mapped[str] = mapped_column(
        Enum("proctored", "practice", name="assessment_mode", create_type=False),
        nullable=False,
        default="practice",
    )
    #: Coverage per competency and item budget, as served.
    blueprint: Mapped[dict | None] = mapped_column(JSONB)
    framework_version_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("framework_versions.id")
    )
    #: The difficulty-weighted score. ``score`` keeps the unweighted
    #: percentage so the two can be shown side by side.
    weighted_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    competency = relationship("Competency", lazy="selectin")


class AssessmentQuestion(Base):
    """A question as served in one assessment, plus the answer given.

    ``is_correct`` is set at submit time by comparing ``selected_index`` with
    the question key. It is never inferred, never model-assisted.
    """

    __tablename__ = "assessment_questions"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("questions.id"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_index: Mapped[int | None] = mapped_column(Integer)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)

    question = relationship("Question", lazy="selectin")
