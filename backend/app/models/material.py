"""M8 · uploaded learning material and its text chunks."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.config import settings
from app.models.base import Base

MATERIAL_STATUS = Enum(
    "UPLOADED",
    "EXTRACTED",
    "CHUNKED",
    "GENERATED",
    "FAILED",
    name="material_status",
    create_type=False,
)


class LearningMaterial(Base):
    """A trainer-uploaded PDF, DOCX or PPTX.

    ``status`` tracks the pipeline stage so the trainer console can show where
    a document got to. ``error`` carries the reason a document failed — a
    scanned PDF with no extractable text says so plainly rather than silently
    producing questions about nothing.
    """

    __tablename__ = "learning_materials"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("auth.users.id")
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    #: The original client-supplied name, kept for display only. The stored
    #: object is named from a server-generated UUID (§13.7).
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(Text, nullable=False)
    competency_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id")
    )
    status: Mapped[str] = mapped_column(MATERIAL_STATUS, default="UPLOADED")
    page_count: Mapped[int | None] = mapped_column(Integer)
    char_count: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    #: Only approved material enters the assistant's corpus: it answers
    #: from the organisation's vetted material, not from whatever
    #: happens to have been uploaded.
    corpus_approved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    language: Mapped[str] = mapped_column(Text, nullable=False, default="en")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    competency = relationship("Competency", lazy="selectin")


class MaterialChunk(Base):
    """One ~800-token window of a document, with its page number preserved.

    The page number travels all the way through to the generated question, so
    a trainer can check any item against the source page it came from.
    """

    __tablename__ = "material_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("learning_materials.id", ondelete="CASCADE")
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_no: Mapped[int | None] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.EMBED_DIM))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
