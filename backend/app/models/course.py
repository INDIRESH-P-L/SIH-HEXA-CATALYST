"""M6 catalogue mirror, enrolments, and M5 recommendation rows."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.config import settings
from app.models.base import Base

CATALOGUE_SOURCE = Enum("IGOT", "NSSTA", name="catalogue_source", create_type=False)
LEARNING_FORMAT = Enum(
    "SELF_PACED",
    "CLASSROOM",
    "BLENDED",
    "VIRTUAL_LAB",
    name="learning_format",
    create_type=False,
)
ENROLLMENT_STATUS = Enum(
    "RECOMMENDED",
    "ENROLLED",
    "NOMINATION_REQUESTED",
    "IN_PROGRESS",
    "COMPLETED",
    name="enrollment_status",
    create_type=False,
)


class Course(Base):
    """Local mirror of a catalogue offering.

    Populated by POST /catalogue/sync from whichever CatalogueProvider is
    configured. Holding a mirror is what lets the application keep serving
    recommendations when the catalogue service is unreachable.
    """

    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="courses_source_external_id_key"),
        CheckConstraint("proficiency_level between 1 and 5", name="ck_proficiency_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(CATALOGUE_SOURCE, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    competency_code: Mapped[str] = mapped_column(Text, nullable=False)
    proficiency_level: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    prerequisites: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    learning_format: Mapped[str] = mapped_column(LEARNING_FORMAT, nullable=False)
    course_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="ACTIVE")
    session_start: Mapped[date | None] = mapped_column(Date)
    seats: Mapped[int | None] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.EMBED_DIM))
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Enrollment(Base):
    """iGOT courses are self-enrolled; NSSTA programmes are nominated for.

    The two paths carry different statuses on purpose: ENROLLED is a completed
    action, NOMINATION_REQUESTED is the opening step of an academy process that
    this prototype does not own.
    """

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="enrollments_user_course_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE")
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(
        ENROLLMENT_STATUS, nullable=False, default="RECOMMENDED"
    )
    external_ref: Mapped[str | None] = mapped_column(Text)
    enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    course = relationship("Course", lazy="selectin")


class Recommendation(Base):
    """One ranked course inside one generated batch.

    ``breakdown`` holds every term of the ranking formula so the interface can
    show the arithmetic. ``explanation`` is the only LLM-written field here and
    is nullable — when the LLM is unavailable the caller substitutes a
    deterministic template rather than leaving the card empty.
    """

    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE")
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE")
    )
    competency_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id")
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    course = relationship("Course", lazy="selectin")
