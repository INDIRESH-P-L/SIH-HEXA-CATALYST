"""The evidence ledger — append-only, and the single source of truth for levels.

Nothing in this application stores a "current level" in a mutable column.
A level is always the most recent evidence row for a (user, competency) pair,
read through the ``user_competency`` view. That is what makes the closed loop
auditable: every level the UI shows can be traced back to the row that produced
it.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

EVIDENCE_SOURCE = Enum(
    "self_declared",
    "assessment",
    "course_completion",
    "admin_set",
    name="evidence_source",
    create_type=False,
)

#: Confidence attached to each kind of evidence (§12).
CONFIDENCE_BY_SOURCE: dict[str, Decimal] = {
    "self_declared": Decimal("0.25"),
    "course_completion": Decimal("0.60"),
    "assessment": Decimal("0.90"),
    "admin_set": Decimal("1.00"),
}

#: A practice attempt is recorded but carries half the weight of a
#: proctored one, and stays out of administrator dashboards.
PRACTICE_CONFIDENCE: Decimal = Decimal("0.50")

#: Completion confidence differs by catalogue: a self-paced iGOT module
#: is weaker evidence than a supervised NSSTA residential programme.
COMPLETION_CONFIDENCE: dict[str, Decimal] = {
    "IGOT": Decimal("0.45"),
    "NSSTA": Decimal("0.80"),
}


class CompetencyEvidence(Base):
    __tablename__ = "competency_evidence"
    __table_args__ = (CheckConstraint("level between 0 and 4", name="ck_evidence_level"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE")
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE")
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    source_type: Mapped[str] = mapped_column(EVIDENCE_SOURCE, nullable=False)
    source_ref: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0.50")
    )
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UserCompetency(Base):
    """Read-only mapping over the ``user_competency`` view.

    SQLAlchemy needs a primary key to map anything; (user_id, competency_id) is
    unique in the view by construction (``distinct on``). Never written to.
    """

    __tablename__ = "user_competency"

    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    competency_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    current_level: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2))
    source_type: Mapped[str] = mapped_column(EVIDENCE_SOURCE)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
