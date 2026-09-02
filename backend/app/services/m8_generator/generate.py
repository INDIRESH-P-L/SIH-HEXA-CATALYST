"""MCQ generation against Groq with a strict JSON schema.

Model choice is not incidental. Constrained decoding — where the provider
guarantees the response parses against the supplied schema — is available on
GPT-OSS and Qwen 3, and not on every hosted model. Generation therefore routes
to ``openai/gpt-oss-20b``. Strict mode additionally requires every
property to appear in ``required`` and every object to set
``additionalProperties: false``, and it cannot be combined with streaming or
tool use.

Three items per chunk, one chunk per request. That is a token-budget decision:
the free tier allows roughly 8,000 tokens per minute, and a single large request
covering the whole document would exceed it and fail the whole generation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import prompts, scrub
from app.ai.llm_client import complete
from app.ai.schemas_json import MCQ_BATCH_SCHEMA
from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import get_logger
from app.services.m8_generator.chunk import Chunk

log = get_logger(__name__)

QUESTIONS_PER_CHUNK = 3

#: How much of a chunk to show the model. Trimmed so a very long chunk cannot
#: blow the per-minute token ceiling on its own.
MAX_EXCERPT_CHARS = 3600

DIFFICULTY_MIXES: dict[str, str] = {
    "balanced": "one easy, one medium, one hard",
    "easy": "all easy",
    "medium": "all medium",
    "hard": "all hard",
}


@dataclass
class GeneratedItem:
    """One item as returned by the model, before validation."""

    question_text: str
    options: list[str]
    correct_index: int
    explanation: str
    difficulty: str
    topic: str
    chunk: Chunk

    @classmethod
    def from_payload(cls, payload: dict[str, Any], chunk: Chunk) -> "GeneratedItem":
        return cls(
            question_text=str(payload.get("question_text", "")).strip(),
            options=[str(o).strip() for o in (payload.get("options") or [])],
            correct_index=int(payload.get("correct_index", -1)),
            explanation=str(payload.get("explanation", "")).strip(),
            difficulty=str(payload.get("difficulty", "")).strip().lower(),
            topic=str(payload.get("topic", "")).strip(),
            chunk=chunk,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "question_text": self.question_text,
            "options": self.options,
            "correct_index": self.correct_index,
            "explanation": self.explanation,
            "difficulty": self.difficulty,
            "topic": self.topic,
        }

    @property
    def embedding_text(self) -> str:
        """What the near-duplicate check compares.

        Stem plus options: two questions on the same fact with different
        distractors are not duplicates, and should not be treated as such.
        """
        return f"{self.question_text} {' '.join(self.options)}"


def build_prompt(
    chunk: Chunk,
    competency_name: str,
    *,
    num_questions: int = QUESTIONS_PER_CHUNK,
    difficulty_mix: str = "balanced",
    retry_reason: str | None = None,
) -> str:
    """Assemble the generation prompt through the scrubber.

    The passage is uploaded training material, not personal data, but it still
    goes through ``build_context`` so that every outbound prompt in the codebase
    is built the same way and the whitelist stays the only door.
    """
    context = scrub.build_context(
        competency_name=competency_name,
        source_excerpt=chunk.content[:MAX_EXCERPT_CHARS],
        num_questions=num_questions,
        difficulty_mix=DIFFICULTY_MIXES.get(difficulty_mix, DIFFICULTY_MIXES["balanced"]),
    )
    prompt = prompts.MCQ_GENERATION.format(**context)
    if retry_reason:
        prompt += prompts.MCQ_RETRY_SUFFIX.format(
            retry_reason=scrub.build_context(retry_reason=retry_reason)["retry_reason"]
        )
    return prompt


async def generate_for_chunk(
    session: AsyncSession,
    *,
    chunk: Chunk,
    competency_name: str,
    user_id: uuid.UUID | None,
    num_questions: int = QUESTIONS_PER_CHUNK,
    difficulty_mix: str = "balanced",
    retry_reason: str | None = None,
) -> list[GeneratedItem]:
    """One request, one chunk. Returns [] when the model is unavailable.

    Never raises for an LLM problem: the caller reports how many items were
    generated, and zero is a legitimate, reportable outcome.
    """
    prompt = build_prompt(
        chunk,
        competency_name,
        num_questions=num_questions,
        difficulty_mix=difficulty_mix,
        retry_reason=retry_reason,
    )

    try:
        payload = await complete(
            session=session,
            purpose="mcq_generation",
            prompt=prompt,
            system=prompts.SYSTEM_MCQ,
            json_schema=MCQ_BATCH_SCHEMA,
            user_id=user_id,
            temperature=0.5,
            max_tokens=2048,
        )
    except AppError as exc:
        log.info("generation unavailable for chunk %d: %s", chunk.index, exc.message)
        return []
    except Exception as exc:  # noqa: BLE001
        log.warning("unexpected generation failure on chunk %d: %s", chunk.index, exc)
        return []

    if not isinstance(payload, dict):
        log.warning("generation returned a non-object payload")
        return []

    raw_items = payload.get("questions") or []
    items = [GeneratedItem.from_payload(item, chunk) for item in raw_items]
    log.info(
        "chunk %d (page %s): model returned %d items via %s",
        chunk.index,
        chunk.page_no,
        len(items),
        settings.MODEL_MCQ,
    )
    return items
