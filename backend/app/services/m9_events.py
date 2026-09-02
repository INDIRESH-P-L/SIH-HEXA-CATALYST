"""M9 · the event backbone.

One append-only stream is what makes every downstream number reconcilable.
Dashboards read marts, marts are rebuilt from events, and an event is never
edited. If a figure on a dashboard is disputed, the answer is to replay the
events that produced it.

Every event is (actor, verb, object, time) plus a payload. Verbs are namespaced
by module so the stream can be filtered without a schema per producer.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.architecture import Event

log = get_logger(__name__)


class Verb:
    """The vocabulary. Adding one is cheap; changing one breaks replay."""

    # M1
    PROFILE_REGISTERED = "profile.registered"
    PROFILE_UPDATED = "profile.updated"
    SESSION_STARTED = "session.started"
    CONSENT_RECORDED = "consent.recorded"

    # M2
    COMPETENCY_DECLARED = "competency.declared"
    FRAMEWORK_SEALED = "framework.sealed"

    # M3
    ASSESSMENT_STARTED = "assessment.started"
    ASSESSMENT_SUBMITTED = "assessment.submitted"
    COMPETENCY_LEVEL_CHANGED = "competency.level_changed"

    # M5
    RECOMMENDATION_GENERATED = "recommendation.generated"
    RECOMMENDATION_SHOWN = "recommendation.shown"
    RECOMMENDATION_CLICKED = "recommendation.clicked"

    # M6
    ENROLMENT_REQUESTED = "enrolment.requested"
    ENROLMENT_CONFIRMED = "enrolment.confirmed"
    NOMINATION_REQUESTED = "nomination.requested"
    NOMINATION_ADVANCED = "nomination.advanced"
    COURSE_COMPLETED = "course.completed"

    # M7
    ASSISTANT_ASKED = "assistant.asked"
    ASSISTANT_REFUSED = "assistant.refused"

    # M8
    MATERIAL_UPLOADED = "material.uploaded"
    QUESTIONS_GENERATED = "questions.generated"
    QUESTION_REVIEWED = "question.reviewed"


async def emit(
    session: AsyncSession,
    *,
    verb: str,
    actor_id: uuid.UUID | None = None,
    object_type: str | None = None,
    object_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Append one event.

    Never raises: an analytics write must not be able to fail the request that
    produced it. A lost event costs a row in a rollup; a failed submit costs an
    officer their assessment.
    """
    try:
        session.add(
            Event(
                actor_id=actor_id,
                verb=verb,
                object_type=object_type,
                object_id=object_id,
                payload=payload or {},
            )
        )
        await session.flush()
    except Exception as exc:  # pragma: no cover - best effort by design
        log.warning("failed to emit event %s: %s", verb, exc)


async def count_by_verb(session: AsyncSession) -> dict[str, int]:
    rows = (
        await session.execute(
            select(Event.verb, func.count()).group_by(Event.verb).order_by(Event.verb)
        )
    ).all()
    return {verb: int(count) for verb, count in rows}


async def recent(
    session: AsyncSession, *, limit: int = 50, actor_id: uuid.UUID | None = None
) -> list[Event]:
    stmt = select(Event).order_by(Event.occurred_at.desc()).limit(limit)
    if actor_id is not None:
        stmt = stmt.where(Event.actor_id == actor_id)
    return list((await session.execute(stmt)).scalars().all())


async def stream_size(session: AsyncSession) -> int:
    return int(await session.scalar(select(func.count()).select_from(Event)) or 0)
