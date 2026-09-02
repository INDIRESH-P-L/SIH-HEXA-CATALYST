"""M7 · Learning & AI Assistant endpoints.

Retrieval-grounded assistance over an approved corpus: cited, and willing to
say it does not know.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.errors import NotConfiguredError
from app.core.security import CurrentUserDep
from app.services import m7_assistant as assistant

router = APIRouter(prefix="/assistant", tags=["M7 · assistant"])


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class CitationRead(BaseModel):
    material_id: str
    material_title: str
    chunk_id: str
    page_no: int | None = None
    excerpt: str
    score: float


class AskResponse(BaseModel):
    """An answer, or a refusal with somewhere to go instead."""

    answer: str
    citations: list[CitationRead]
    grounded: bool
    refused: bool
    refusal_reason: str | None = None
    retrieval_score: float
    source: str = Field(
        description="'ai' when the model wrote it, 'extract' on fallback, "
        "'grounding_gate' when refused."
    )
    suggested_course: dict[str, Any] | None = None
    latency_ms: int
    note: str = Field(
        default=(
            "Answers are drawn only from approved training material, with "
            "citations. Where the corpus does not cover a question the "
            "assistant refuses and names the course that does, rather than "
            "answering from general knowledge."
        )
    )


class CorpusStats(BaseModel):
    approved_materials: int
    indexed_chunks: int
    grounding_threshold: float
    enabled: bool


@router.get("/corpus", response_model=CorpusStats, summary="What the assistant can answer from")
async def corpus(
    _user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CorpusStats:
    stats = await assistant.corpus_stats(session)
    return CorpusStats(
        approved_materials=stats["approved_materials"],
        indexed_chunks=stats["indexed_chunks"],
        grounding_threshold=assistant.GROUNDING_THRESHOLD,
        enabled=assistant.is_enabled(),
    )


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask a question about the approved training material",
)
async def ask(
    payload: AskRequest,
    user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AskResponse:
    """Answer from the approved corpus, with citations, or refuse and route.

    The refusal branch is deliberate. For methodology questions — sampling
    design, national accounts, price index construction — a confident wrong
    answer is worse than no answer.
    """
    if not assistant.is_enabled():
        raise NotConfiguredError(
            "The assistant is disabled in this deployment. Set "
            "ASSISTANT_ENABLED=true to turn it on; it answers only from "
            "material a trainer has approved into the corpus."
        )

    result = await assistant.ask(session, profile=user.profile, question=payload.question)
    await session.commit()

    return AskResponse(
        answer=result.answer,
        citations=[CitationRead(**c.as_dict()) for c in result.citations],
        grounded=result.grounded,
        refused=result.refused,
        refusal_reason=result.refusal_reason,
        retrieval_score=result.retrieval_score,
        source=result.source,
        suggested_course=result.suggested_course,
        latency_ms=result.latency_ms,
    )
