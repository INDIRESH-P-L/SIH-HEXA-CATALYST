"""Tables introduced by the nine-module reference architecture.

Grouped here rather than scattered across the existing model files because
they belong to one another: framework versioning, the activity layer, the
attribute resolver, gap snapshots, the outbox, the nomination state machine
and the event store are all part of the same design decision — that every
number on screen should be derivable on demand from stored, versioned facts.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
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

from app.models.base import Base

REQUIREMENT_HORIZON = Enum(
    "current_role", "next_role", name="requirement_horizon", create_type=False
)
COMPETENCY_KIND = Enum(
    "knowledge", "skill", "attribute", name="competency_kind", create_type=False
)
DECAY_CLASS = Enum(
    "tools_platforms",
    "regulatory_procedural",
    "methodology",
    "behavioural",
    name="decay_class",
    create_type=False,
)
ATTRIBUTE_SOURCE = Enum(
    "sso_claim",
    "hr_record",
    "self_declared",
    "certificate",
    "admin_override",
    name="attribute_source",
    create_type=False,
)
ASSESSMENT_MODE = Enum("proctored", "practice", name="assessment_mode", create_type=False)
OUTBOX_STATUS = Enum(
    "PENDING", "SENT", "FAILED", "ABANDONED", name="outbox_status", create_type=False
)
NOMINATION_STATE = Enum(
    "REQUESTED",
    "SUPERVISOR_APPROVED",
    "CBU_APPROVED",
    "ACADEMY_CONFIRMED",
    "REJECTED",
    name="nomination_state",
    create_type=False,
)


# ── M2 · framework versioning and the activity layer ─────────────────────────


class FrameworkVersion(Base):
    """An immutable snapshot of the competency framework.

    Sealing a version is what makes a past dashboard reproducible and training
    effectiveness measurable. Without it, a dashboard from last quarter
    silently rewrites itself when the framework changes.
    """

    __tablename__ = "framework_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    version: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    sealed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Activity(Base):
    """A concrete action a role performs, toward one outcome.

    FRAC is Position → Role → Activity → Competency. The activity layer is what
    lets a gap be explained as "you cannot yet do this part of your job"
    rather than as an abstract score.
    """

    __tablename__ = "activities"
    __table_args__ = (UniqueConstraint("job_role_id", "code", name="activities_role_code_key"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    job_role_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("job_roles.id", ondelete="CASCADE")
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    competencies = relationship("ActivityCompetency", lazy="selectin")


class ActivityCompetency(Base):
    __tablename__ = "activity_competencies"

    activity_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True
    )
    required_level: Mapped[int] = mapped_column(Integer, nullable=False)

    competency = relationship("Competency", lazy="selectin")


# ── M1 · the attribute resolver ──────────────────────────────────────────────


class ProfileAttribute(Base):
    """One claim about an officer, from one source, at one point in time.

    Four sources routinely disagree about a designation. Storing a single value
    loses the disagreement. Storing each claim with its source, confidence and
    effective date lets the resolver choose, lets an administrator correct, and
    lets an officer see exactly why their record reads as it does.

    Correction is appended as a new row. Nothing is ever overwritten.
    """

    __tablename__ = "profile_attributes"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE")
    )
    attribute: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(ATTRIBUTE_SOURCE, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0.50")
    )
    effective_from: Mapped[date | None] = mapped_column(Date)
    superseded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ConsentRecord(Base):
    """DPDP Act 2023: a consent artefact recorded per stated purpose."""

    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE")
    )
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    policy_version: Mapped[str] = mapped_column(Text, nullable=False, default="v1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ── M3 · cut-scores ──────────────────────────────────────────────────────────


class CompetencyCutScore(Base):
    """SME-set band boundaries, per competency.

    Never one global threshold: 60% on sampling theory and 60% on spreadsheet
    hygiene are not the same statement about an officer.
    """

    __tablename__ = "competency_cut_scores"

    competency_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True
    )
    level_1_min: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    level_2_min: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    level_3_min: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    level_4_min: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    method: Mapped[str] = mapped_column(Text, nullable=False, default="modified_angoff")
    set_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ── M4 · gap snapshots ───────────────────────────────────────────────────────


class GapSnapshot(Base):
    """A gap analysis frozen against a framework version and a date.

    So that a dashboard from last quarter recomputes to exactly the same
    numbers, which is the precondition for measuring whether training worked.
    """

    __tablename__ = "gap_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE")
    )
    framework_version_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("framework_versions.id")
    )
    taken_on: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    rows: Mapped[list] = mapped_column("rows", JSONB, nullable=False)
    summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ── M6 · outbox and nominations ──────────────────────────────────────────────


class OutboxEntry(Base):
    """A write queued for an external system.

    The platform keeps working when the API does not: an enrolment or
    nomination is recorded locally, queued idempotently, and retried. Nothing
    is lost because an upstream was down.
    """

    __tablename__ = "outbox"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    idempotency_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE")
    )
    operation: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(OUTBOX_STATUS, nullable=False, default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    external_ref: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Nomination(Base):
    """An NSSTA nomination and the state it has reached.

    requested → supervisor approved → CBU approved → academy confirmed, with
    rejection available at every step. The platform owns the request; the
    approvals belong to people, and the state machine says so.
    """

    __tablename__ = "nominations"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="nominations_user_course_key"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE")
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE")
    )
    state: Mapped[str] = mapped_column(NOMINATION_STATE, nullable=False, default="REQUESTED")
    justification: Mapped[str | None] = mapped_column(Text)
    external_ref: Mapped[str | None] = mapped_column(Text)
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id")
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    course = relationship("Course", lazy="selectin")


class TagCrosswalk(Base):
    """External catalogue tag → internal competency.

    Unmapped tags queue for administrator review rather than being silently
    dropped, because a silently dropped tag is a course that never surfaces.
    """

    __tablename__ = "tag_crosswalk"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    external_tag: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    competency_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id")
    )
    reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ── M7 · assistant ───────────────────────────────────────────────────────────


class AssistantQuery(Base):
    """One question asked of the grounded assistant, and what happened.

    Refusals are recorded as deliberately as answers: "this is not in the
    approved corpus" is the correct behaviour, and its rate is a quality
    signal about the corpus rather than about the model.
    """

    __tablename__ = "assistant_queries"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE")
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text)
    citations: Mapped[list | None] = mapped_column(JSONB)
    retrieval_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    grounded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    refused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    refusal_reason: Mapped[str | None] = mapped_column(Text)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ── M9 · event store and marts ───────────────────────────────────────────────


class Event(Base):
    """One append-only fact: actor, verb, object, time.

    Dashboards read marts; marts are rebuilt from events; an event is never
    edited. That is what makes every downstream number reconcilable.
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id")
    )
    verb: Mapped[str] = mapped_column(Text, nullable=False)
    object_type: Mapped[str | None] = mapped_column(Text)
    object_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    payload: Mapped[dict | None] = mapped_column(JSONB)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class MartCompetency(Base):
    __tablename__ = "mart_competency"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    job_role_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("job_roles.id")
    )
    competency_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id")
    )
    framework_version_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("framework_versions.id")
    )
    officers: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_current_level: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    avg_required_level: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    officers_with_gap: Mapped[int] = mapped_column(Integer, nullable=False)
    built_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MartTrainingEffectiveness(Base):
    __tablename__ = "mart_training_effectiveness"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("courses.id")
    )
    cohort: Mapped[str | None] = mapped_column(Text)
    attendees: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_level_before: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    avg_level_after: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    avg_delta: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    comparison_delta: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    built_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
