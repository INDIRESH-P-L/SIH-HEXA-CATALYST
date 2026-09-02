"""M8 · learning material models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MaterialStatusName = Literal["UPLOADED", "EXTRACTED", "CHUNKED", "GENERATED", "FAILED"]


class MaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    filename: str
    file_type: str
    competency_id: uuid.UUID | None = None
    competency_code: str | None = None
    competency_name: str | None = None
    status: MaterialStatusName
    page_count: int | None = None
    char_count: int | None = None
    chunk_count: int | None = None
    question_count: int | None = None
    approved_count: int | None = None
    error: str | None = None
    created_at: datetime | None = None


class GenerateQuestionsRequest(BaseModel):
    """POST /materials/{id}/generate."""

    num_questions: int = Field(
        default=12,
        ge=1,
        le=30,
        description=(
            "Items to attempt. Generation runs one chunk per request at three "
            "items per chunk to stay under the provider's per-minute token "
            "ceiling."
        ),
    )
    difficulty_mix: str = Field(
        default="balanced",
        description="balanced | easy | medium | hard",
    )
    auto_approve_passing: bool = Field(
        default=False,
        description=(
            "Approve items that pass every validation check without trainer "
            "review. Off by default: a human should see the bank first."
        ),
    )


class ChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chunk_index: int
    page_no: int | None = None
    content: str
    char_count: int
