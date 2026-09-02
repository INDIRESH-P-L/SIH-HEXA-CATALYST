"""M8 · generated multiple-choice questions."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.config import settings
from app.models.base import Base

QUESTION_STATUS = Enum(
    "DRAFT", "APPROVED", "REJECTED", name="question_status", create_type=False
)


class Question(Base):
    """One generated item.

    The stem, options and explanation are LLM-written. Everything that decides
    whether the item is usable — the ``validation`` verdict — is computed by
    deterministic code with no model involved (§11.4).

    Items land as DRAFT. A trainer promotes them to APPROVED, and only APPROVED
    items are ever served in a quiz.
    """

    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint("correct_index between 0 and 3", name="ck_correct_index"),
        CheckConstraint(
            "difficulty in ('easy','medium','hard')", name="ck_question_difficulty"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    material_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("learning_materials.id", ondelete="CASCADE")
    )
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("material_chunks.id")
    )
    competency_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id")
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    #: Exactly four strings.
    options: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(QUESTION_STATUS, default="DRAFT")
    #: Per-check pass/fail from the validation gate, surfaced in the trainer UI.
    validation: Mapped[dict | None] = mapped_column(JSONB)
    source_page: Mapped[int | None] = mapped_column(Integer)
    #: The exact span the item was generated from, so a reviewer can
    #: always see where a question came from.
    source_span: Mapped[str | None] = mapped_column(Text)
    bloom_level: Mapped[str | None] = mapped_column(Text)
    #: Item parameters learned from live responses. The authored
    #: difficulty is the launch estimate; the observed value replaces
    #: it once enough responses exist.
    difficulty_b: Mapped[Decimal | None] = mapped_column(Numeric(5, 3))
    discrimination_a: Mapped[Decimal | None] = mapped_column(Numeric(5, 3))
    times_served: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    times_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    #: Rejected items are kept and reused as negative examples in later
    #: generation prompts, so the generator improves with each review.
    is_negative_example: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    #: Used for near-duplicate detection against the existing bank.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.EMBED_DIM))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    competency = relationship("Competency", lazy="selectin")
