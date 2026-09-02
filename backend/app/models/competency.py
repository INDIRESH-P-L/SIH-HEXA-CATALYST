"""M2 · competency framework tables."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.config import settings
from app.models.base import Base

COMPETENCY_CLUSTER = Enum(
    "STATISTICAL",
    "TECHNICAL",
    "DIGITAL_GOVERNANCE",
    "BEHAVIOURAL",
    name="competency_cluster",
    create_type=False,
)


class Competency(Base):
    __tablename__ = "competencies"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    cluster: Mapped[str] = mapped_column(COMPETENCY_CLUSTER, nullable=False)
    #: The embedding is built from this text, so it has to read like real prose.
    description: Mapped[str] = mapped_column(Text, nullable=False)
    frac_type: Mapped[str | None] = mapped_column(Text, default="domain")
    #: FRAC competency typing: knowledge, skill or attribute.
    kind: Mapped[str] = mapped_column(
        Enum("knowledge", "skill", "attribute", name="competency_kind", create_type=False),
        nullable=False,
        default="skill",
    )
    #: How fast this competency goes stale. Behavioural ones do not.
    decay: Mapped[str] = mapped_column(
        Enum(
            "tools_platforms",
            "regulatory_procedural",
            "methodology",
            "behavioural",
            name="decay_class",
            create_type=False,
        ),
        nullable=False,
        default="methodology",
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.EMBED_DIM))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RoleCompetencyRequirement(Base):
    __tablename__ = "role_competency_requirements"
    __table_args__ = (
        CheckConstraint("required_level between 1 and 4", name="ck_required_level"),
        CheckConstraint("criticality between 1.0 and 3.0", name="ck_criticality"),
    )

    job_role_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("job_roles.id", ondelete="CASCADE"), primary_key=True
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True
    )
    required_level: Mapped[int] = mapped_column(Integer, nullable=False)
    criticality: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("1.00")
    )
    #: Needed in the current post, or the next one up? A next-role
    #: requirement is real but discounted rather than ignored.
    horizon: Mapped[str] = mapped_column(
        Enum("current_role", "next_role", name="requirement_horizon", create_type=False),
        nullable=False,
        default="current_role",
    )
    framework_version_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("framework_versions.id")
    )

    job_role = relationship("JobRole", back_populates="requirements")
    competency = relationship("Competency", lazy="selectin")
