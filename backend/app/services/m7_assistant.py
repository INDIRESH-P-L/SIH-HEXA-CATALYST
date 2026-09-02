"""M7 · Learning & AI Assistant.

Action layer. Retrieval-grounded assistance over an approved corpus: cited,
and willing to say it does not know.

The assistant answers from the organisation's own approved material, not from
whatever the model happens to remember. That is what makes it usable for
methodology questions — sampling design, national accounts, price index
construction — where a confident wrong answer is worse than no answer at all.

The refusal branch is a feature, not a failure mode. Saying "this is not in the
approved corpus, here is the course that covers it" is the correct behaviour,
and its rate is a quality signal about the corpus rather than about the model.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import embeddings, prompts, scrub
from app.ai.llm_client import complete
from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import get_logger
from app.models.architecture import AssistantQuery
from app.models.course import Course
from app.models.material import LearningMaterial, MaterialChunk
from app.models.user import Profile
from app.services import m2_framework as framework
from app.services import m4_gap_engine as engine
from app.services import m9_events as events

log = get_logger(__name__)

#: How many chunks each retriever returns before fusion.
RETRIEVE_K = 12
#: How many survive reranking and reach the prompt.
CONTEXT_K = 4

#: Below this similarity the corpus does not support an answer and the
#: assistant refuses.
#:
#: Calibrated against the model actually in use rather than guessed. bge-small
#: produces a narrow range: on-topic questions against this corpus score
#: 0.58-0.75, while a question with nothing to do with the material still
#: scores around 0.36 because both texts are English prose. A threshold set at
#: the bottom of that noise floor admits exactly the confident wrong answers
#: the gate exists to prevent, so it sits above it.
GROUNDING_THRESHOLD = 0.50

#: Characters of each chunk shown to the model. Chunks are ~3200 chars.
MAX_CHUNK_CHARS = 4000


@dataclass
class Citation:
    """Where one claim came from."""

    material_id: uuid.UUID
    material_title: str
    chunk_id: uuid.UUID
    page_no: int | None
    excerpt: str
    score: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "material_id": str(self.material_id),
            "material_title": self.material_title,
            "chunk_id": str(self.chunk_id),
            "page_no": self.page_no,
            "excerpt": self.excerpt,
            "score": round(self.score, 4),
        }


@dataclass
class AssistantAnswer:
    """The result of one question."""

    answer: str
    citations: list[Citation] = field(default_factory=list)
    grounded: bool = False
    refused: bool = False
    refusal_reason: str | None = None
    retrieval_score: float = 0.0
    source: str = "template"
    suggested_course: dict[str, Any] | None = None
    latency_ms: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": [c.as_dict() for c in self.citations],
            "grounded": self.grounded,
            "refused": self.refused,
            "refusal_reason": self.refusal_reason,
            "retrieval_score": round(self.retrieval_score, 4),
            "source": self.source,
            "suggested_course": self.suggested_course,
            "latency_ms": self.latency_ms,
        }


# ── corpus retrieval ─────────────────────────────────────────────────────────


async def _dense_chunks(
    session: AsyncSession, question: str, limit: int
) -> list[tuple[uuid.UUID, float]]:
    """Semantic neighbours among approved chunks."""
    vector = embeddings.embed_one(question)
    rows = (
        await session.execute(
            text(
                "select c.id, 1 - (c.embedding <=> cast(:emb as vector(384))) as score "
                "from material_chunks c "
                "join learning_materials m on m.id = c.material_id "
                "where m.corpus_approved = true and c.embedding is not null "
                "order by c.embedding <=> cast(:emb as vector(384)) "
                "limit :k"
            ),
            {"emb": embeddings.to_pgvector(vector), "k": limit},
        )
    ).all()
    return [(chunk_id, float(score)) for chunk_id, score in rows]


async def _lexical_chunks(
    session: AsyncSession, question: str, limit: int
) -> list[tuple[uuid.UUID, float]]:
    """Exact-term match, for the acronyms an embedding smooths away."""
    rows = (
        await session.execute(
            text(
                "select c.id, ts_rank(c.search_tsv, plainto_tsquery('english', :q)) as score "
                "from material_chunks c "
                "join learning_materials m on m.id = c.material_id "
                "where m.corpus_approved = true "
                "  and c.search_tsv @@ plainto_tsquery('english', :q) "
                "order by score desc limit :k"
            ),
            {"q": question, "k": limit},
        )
    ).all()
    return [(chunk_id, float(score)) for chunk_id, score in rows]


def _fuse(
    dense: list[tuple[uuid.UUID, float]],
    lexical: list[tuple[uuid.UUID, float]],
    *,
    k: int = 60,
) -> dict[uuid.UUID, float]:
    """Reciprocal rank fusion over the two retrievers."""
    fused: dict[uuid.UUID, float] = {}
    for ranking in (dense, lexical):
        for rank, (chunk_id, _score) in enumerate(ranking, start=1):
            fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return fused


def _rerank(
    fused: dict[uuid.UUID, float], dense_scores: dict[uuid.UUID, float]
) -> list[tuple[uuid.UUID, float]]:
    """Order by fused rank, breaking ties on raw semantic similarity.

    A cross-encoder would do better and is the documented upgrade path; it is
    not shipped here because a second model on the request path is a cost this
    prototype has not earned.
    """
    scored = [
        (chunk_id, score + 0.001 * dense_scores.get(chunk_id, 0.0))
        for chunk_id, score in fused.items()
    ]
    scored.sort(key=lambda entry: -entry[1])
    return scored


async def retrieve(
    session: AsyncSession, question: str
) -> tuple[list[Citation], float]:
    """Hybrid retrieval over the approved corpus.

    Returns the surviving citations and a normalised confidence in them. An
    empty corpus returns no citations and zero confidence, which routes to the
    refusal branch rather than to an ungrounded answer.
    """
    dense = await _dense_chunks(session, question, RETRIEVE_K)
    lexical = await _lexical_chunks(session, question, RETRIEVE_K)
    if not dense and not lexical:
        return [], 0.0

    dense_scores = dict(dense)
    ordered = _rerank(_fuse(dense, lexical), dense_scores)[:CONTEXT_K]
    if not ordered:
        return [], 0.0

    chunk_ids = [chunk_id for chunk_id, _ in ordered]
    rows = (
        await session.execute(
            select(MaterialChunk, LearningMaterial)
            .join(LearningMaterial, LearningMaterial.id == MaterialChunk.material_id)
            .where(MaterialChunk.id.in_(chunk_ids))
        )
    ).all()
    by_id = {chunk.id: (chunk, material) for chunk, material in rows}

    citations: list[Citation] = []
    for chunk_id, _fused_score in ordered:
        entry = by_id.get(chunk_id)
        if entry is None:
            continue
        chunk, material = entry
        citations.append(
            Citation(
                material_id=material.id,
                material_title=material.title,
                chunk_id=chunk.id,
                page_no=chunk.page_no,
                excerpt=chunk.content[:MAX_CHUNK_CHARS],
                score=dense_scores.get(chunk_id, 0.0),
            )
        )

    # Fused rank decides what is *considered*; similarity decides what is shown
    # first. A reader checking a citation wants the passage most about their
    # question at the top, and the extractive fallback quotes citations[0].
    citations.sort(key=lambda c: -c.score)

    # Confidence is the best semantic match among survivors.
    confidence = max((c.score for c in citations), default=0.0)
    return citations, confidence


async def _suggest_course(
    session: AsyncSession, question: str
) -> dict[str, Any] | None:
    """The 'route' half of refuse-and-route.

    Refusing without an alternative is unhelpful. Refusing with the course that
    covers the topic is the behaviour that makes refusal acceptable.
    """
    try:
        vector = embeddings.embed_one(question)
        row = (
            await session.execute(
                text(
                    "select course_id, title, source, similarity from match_courses("
                    "cast(:emb as vector(384)), 1, 0.25)"
                ),
                {"emb": embeddings.to_pgvector(vector)},
            )
        ).mappings().first()
    except Exception as exc:  # noqa: BLE001
        log.warning("course suggestion failed: %s", exc)
        return None
    if row is None:
        return None
    return {
        "course_id": str(row["course_id"]),
        "title": row["title"],
        "source": row["source"],
        "similarity": round(float(row["similarity"]), 3),
    }


# ── the query path ───────────────────────────────────────────────────────────


async def ask(
    session: AsyncSession, *, profile: Profile, question: str
) -> AssistantAnswer:
    """Answer a question from the approved corpus, or refuse and route."""
    started = time.perf_counter()
    cleaned = question.strip()

    citations, confidence = await retrieve(session, cleaned)

    # ── the grounding gate ───────────────────────────────────────────────────
    if not citations or confidence < GROUNDING_THRESHOLD:
        suggestion = await _suggest_course(session, cleaned)
        reason = (
            "No approved material covers this question."
            if not citations
            else f"The closest approved material scored {confidence:.2f}, below the "
            f"{GROUNDING_THRESHOLD:.2f} grounding threshold."
        )
        answer = AssistantAnswer(
            answer=(
                "This is not covered by the approved training material available to "
                "me, so I will not answer from general knowledge."
                + (
                    f" The course that covers it is “{suggestion['title']}”."
                    if suggestion
                    else ""
                )
            ),
            citations=citations,
            grounded=False,
            refused=True,
            refusal_reason=reason,
            retrieval_score=confidence,
            source="grounding_gate",
            suggested_course=suggestion,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        await _record(session, profile.id, cleaned, answer)
        await events.emit(
            session,
            verb=events.Verb.ASSISTANT_REFUSED,
            actor_id=profile.id,
            payload={"retrieval_score": round(confidence, 3)},
        )
        return answer

    # ── learner context: the assistant knows who is asking ───────────────────
    context_note = await _learner_context(session, profile)

    excerpt = "\n\n".join(
        f"[{index}] {c.material_title}"
        + (f", page {c.page_no}" if c.page_no else "")
        + f"\n{c.excerpt}"
        for index, c in enumerate(citations, start=1)
    )

    try:
        context = scrub.build_context(
            source_excerpt=excerpt,
            topic=cleaned,
            competency_name=context_note or "unspecified",
        )
        result = await complete(
            session=session,
            purpose="assistant",
            prompt=prompts.ASSISTANT.format(
                source_excerpt=context["source_excerpt"], topic=context["topic"]
            ),
            system=prompts.SYSTEM_ASSISTANT,
            user_id=profile.id,
            temperature=0.2,
            max_tokens=400,
        )
        body = result if isinstance(result, str) else str(result)
        source = "ai"
    except AppError as exc:
        log.info("assistant fell back to extract: %s", exc.message)
        body = _extractive_fallback(citations)
        source = "extract"
    except Exception as exc:  # noqa: BLE001
        log.warning("unexpected assistant failure: %s", exc)
        body = _extractive_fallback(citations)
        source = "extract"

    answer = AssistantAnswer(
        answer=body.strip(),
        citations=citations,
        grounded=True,
        refused=False,
        retrieval_score=confidence,
        source=source,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
    await _record(session, profile.id, cleaned, answer)
    await events.emit(
        session,
        verb=events.Verb.ASSISTANT_ASKED,
        actor_id=profile.id,
        payload={"retrieval_score": round(confidence, 3), "source": source},
    )
    return answer


def _extractive_fallback(citations: list[Citation]) -> str:
    """With no model available, quote the corpus rather than inventing prose.

    Less fluent, still correct, still cited — which is the right trade when the
    alternative is nothing.
    """
    lead = max(citations, key=lambda c: c.score)
    passage = lead.excerpt.strip()
    if len(passage) > 700:
        passage = passage[:700].rsplit(". ", 1)[0] + "."
    where = lead.material_title + (f", page {lead.page_no}" if lead.page_no else "")
    return (
        "The language model is unavailable, so here is the relevant passage from "
        f"the approved material verbatim.\n\nFrom {where}:\n\n{passage}"
    )


async def _learner_context(session: AsyncSession, profile: Profile) -> str | None:
    """The officer's largest current gap, injected into the query context.

    So that "what should I do next" has a real answer rather than a generic one.
    """
    if profile.job_role_id is None:
        return None
    try:
        requirements = await framework.load_requirement_specs(session, profile.job_role_id)
        observations = await framework.load_observations(session, profile.id)
        rows = engine.build_gap_rows(requirements, observations)
        targets = engine.target_gaps(rows, limit=1)
        return targets[0].competency_name if targets else None
    except Exception:  # noqa: BLE001 - context is a nicety, not a requirement
        return None


async def _record(
    session: AsyncSession, user_id: uuid.UUID, question: str, answer: AssistantAnswer
) -> None:
    """Log the exchange. Refusals are recorded as deliberately as answers."""
    session.add(
        AssistantQuery(
            user_id=user_id,
            question=question,
            answer=answer.answer,
            citations=[c.as_dict() for c in answer.citations],
            retrieval_score=Decimal(str(round(answer.retrieval_score, 3))),
            grounded=answer.grounded,
            refused=answer.refused,
            refusal_reason=answer.refusal_reason,
            latency_ms=answer.latency_ms,
        )
    )
    await session.flush()


async def corpus_stats(session: AsyncSession) -> dict[str, int]:
    """What the assistant can actually answer from."""
    from sqlalchemy import func

    materials = await session.scalar(
        select(func.count())
        .select_from(LearningMaterial)
        .where(LearningMaterial.corpus_approved.is_(True))
    )
    chunks = await session.scalar(
        select(func.count())
        .select_from(MaterialChunk)
        .join(LearningMaterial, LearningMaterial.id == MaterialChunk.material_id)
        .where(LearningMaterial.corpus_approved.is_(True))
    )
    return {"approved_materials": int(materials or 0), "indexed_chunks": int(chunks or 0)}


def is_enabled() -> bool:
    return settings.ASSISTANT_ENABLED
