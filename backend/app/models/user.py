"""M1 · identity and profile tables."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

APP_ROLE = Enum("employee", "trainer", "admin", name="app_role", create_type=False)
CADRE_TYPE = Enum("ISS", "SSS", "STATE", "OTHER", name="cadre_type", create_type=False)


class AuthUser(Base):
    """Mirror of ``auth.users``.

    On Supabase this table belongs to Supabase Auth; locally it is created by
    ``000_local_auth_shim.sql``. Mapped so the local auth backend can read and
    write it. The Supabase auth backend never touches it — GoTrue owns it there.
    """

    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class JobRole(Base):
    __tablename__ = "job_roles"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    cadre: Mapped[str] = mapped_column(CADRE_TYPE, nullable=False, default="ISS")
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    requirements = relationship(
        "RoleCompetencyRequirement", back_populates="job_role", lazy="selectin"
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True
    )
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    employee_code: Mapped[str | None] = mapped_column(Text, unique=True)
    designation: Mapped[str | None] = mapped_column(Text)
    department: Mapped[str | None] = mapped_column(
        Text, default="Ministry of Statistics and Programme Implementation"
    )
    station: Mapped[str | None] = mapped_column(Text)
    job_role_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("job_roles.id")
    )
    cadre: Mapped[str | None] = mapped_column(CADRE_TYPE, default="ISS")
    years_experience: Mapped[int | None] = mapped_column(Integer, default=0)
    education: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    job_role = relationship("JobRole", lazy="selectin")


class UserRole(Base):
    """RBAC assignment.

    Roles are read from here server-side on every request. They are never
    trusted from a client-supplied token claim (§13.3).
    """

    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(APP_ROLE, primary_key=True, default="employee")
