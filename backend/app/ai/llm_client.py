"""The single Groq chokepoint.

Every LLM call in this codebase goes through :func:`complete`. Nothing else
imports the ``groq`` package. That is what makes the caching, the audit trail
and the PII assertion impossible to bypass by accident.

Model routing (§8.2)
--------------------
Strict JSON schema output — constrained decoding, guaranteed-parsable — is
supported on GPT-OSS and Qwen 3, and not on every hosted model. So MCQ
generation uses ``openai/gpt-oss-20b``, the prose jobs use
``openai/gpt-oss-120b``, and ``openai/gpt-oss-20b`` doubles as the rate-limit
fallback. Groq has since retired the Llama 3.x models this originally routed
to, which is exactly why the choice lives in settings rather than in code.

Free-tier reality
-----------------
Roughly 30 requests/minute, 1,000/day, 8,000 tokens/minute, 200,000 tokens/day.
MCQ generation is what hits the per-minute token ceiling, which is why
generation sends one chunk per request and why the cache exists.

Failure behaviour
-----------------
On total failure this raises :class:`LLMUnavailable`. Every caller catches it
and substitutes a deterministic fallback. An LLM outage degrades the wording of
the product, never its function.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import prompts, scrub
from app.core.config import settings
from app.core.errors import LLMUnavailable
from app.core.logging import get_logger
from app.models.ai import LLMAudit, LLMCache

log = get_logger(__name__)

Purpose = Literal["mcq_generation", "explanation", "feedback", "assistant"]

#: Which model serves which job.
MODELS: dict[str, str] = {
    "mcq_generation": settings.MODEL_MCQ,
    "explanation": settings.MODEL_TEXT,
    "feedback": settings.MODEL_TEXT,
    "assistant": settings.MODEL_TEXT,
    "fallback": settings.MODEL_FALLBACK,
}

#: How long to wait before the single retry after a rate-limit response.
RATE_LIMIT_BACKOFF_S = 2.0

_client: Any = None


def get_client() -> Any:
    """Lazily construct the Groq client. Raises if no key is configured."""
    global _client
    if not settings.llm_configured:
        raise LLMUnavailable(
            "No GROQ_API_KEY configured; AI features are serving their "
            "deterministic fallbacks."
        )
    if _client is None:
        from groq import AsyncGroq

        _client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=settings.LLM_TIMEOUT_S)
    return _client


def reset_client() -> None:
    """Drop the cached client. Used by tests."""
    global _client
    _client = None


def model_for(purpose: str) -> str:
    return MODELS.get(purpose, settings.MODEL_TEXT)


def cache_key(model: str, purpose: str, prompt: str, system: str | None) -> str:
    """sha256 over the exact inputs that determine the response."""
    material = "␟".join(
        [prompts.PROMPT_VERSION, model, purpose, system or "", prompt]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _is_rate_limit(exc: Exception) -> bool:
    """Detect a rate-limit condition without importing groq at module scope."""
    name = type(exc).__name__
    if name in {"RateLimitError", "APIStatusError"}:
        if getattr(exc, "status_code", None) == 429 or name == "RateLimitError":
            return True
    return "rate limit" in str(exc).lower() or "429" in str(exc)


async def _write_audit(
    session: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    purpose: str,
    model: str,
    key: str,
    preview: str,
    latency_ms: int,
    cache_hit: bool,
    success: bool,
    error: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> None:
    """Record one attempt. Never allowed to break the caller.

    Written on every path — hits, misses, retries and failures — so the audit
    is a record of what was asked, not only of what was billed.
    """
    try:
        session.add(
            LLMAudit(
                user_id=user_id,
                purpose=purpose,
                model=model,
                prompt_hash=key,
                prompt_preview=preview[:500],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cache_hit=cache_hit,
                success=success,
                error=(error[:500] if error else None),
            )
        )
        await session.flush()
    except Exception as exc:  # pragma: no cover - audit must never fail a request
        log.warning("failed to write llm_audit row: %s", exc)


async def _read_cache(session: AsyncSession, key: str) -> dict[str, Any] | None:
    if not settings.LLM_CACHE_ENABLED:
        return None
    row = await session.scalar(select(LLMCache).where(LLMCache.cache_key == key))
    return dict(row.response) if row else None


async def _write_cache(
    session: AsyncSession, key: str, model: str, purpose: str, payload: dict[str, Any]
) -> None:
    if not settings.LLM_CACHE_ENABLED:
        return
    try:
        existing = await session.get(LLMCache, key)
        if existing is None:
            session.add(
                LLMCache(cache_key=key, model=model, purpose=purpose, response=payload)
            )
            await session.flush()
    except Exception as exc:  # pragma: no cover
        log.warning("failed to write llm_cache row: %s", exc)


async def _call_groq(
    *,
    model: str,
    prompt: str,
    system: str | None,
    json_schema: dict[str, Any] | None,
    temperature: float,
    max_tokens: int,
) -> tuple[str, int | None, int | None]:
    """One request to Groq. Returns (text, input_tokens, output_tokens)."""
    client = get_client()

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # GPT-OSS models think before they answer, and the reasoning is billed
    # against the same max_tokens budget as the visible reply. Left at the
    # default, a verbose chain of thought can consume the whole allowance and
    # the response comes back successful but *empty* — which every caller here
    # reads as "the model had nothing to say" and quietly substitutes a
    # template. Asking for low effort keeps the budget for the answer; the
    # prose these calls produce needs none of the deliberation.
    if "gpt-oss" in model:
        kwargs["reasoning_effort"] = "low"

    if json_schema is not None:
        # Structured outputs cannot be combined with streaming or tool use.
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": json_schema.get("name", "response"),
                "strict": True,
                "schema": json_schema["schema"],
            },
        }

    resp = await client.chat.completions.create(**kwargs)
    choice = resp.choices[0]
    content = choice.message.content or ""
    if not content.strip():
        # Callers treat empty as "no answer" and fall back to a template. Say so
        # here, with the finish reason, so a systematic cause — a token budget
        # spent on reasoning, a content filter — is visible in the log instead
        # of looking like the model simply declining.
        log.warning(
            "empty completion: model=%s finish_reason=%s max_tokens=%d",
            model,
            getattr(choice, "finish_reason", "?"),
            max_tokens,
        )
    usage = getattr(resp, "usage", None)
    return (
        content,
        getattr(usage, "prompt_tokens", None) if usage else None,
        getattr(usage, "completion_tokens", None) if usage else None,
    )


async def complete(
    *,
    session: AsyncSession,
    purpose: str,
    prompt: str,
    system: str | None = None,
    json_schema: dict[str, Any] | None = None,
    user_id: uuid.UUID | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> dict[str, Any] | str:
    """Run one LLM call through cache, retry, audit and the PII assertion.

    Returns a parsed ``dict`` when ``json_schema`` is supplied, otherwise the
    response text. Raises :class:`LLMUnavailable` when nothing could be served;
    callers are expected to catch it and fall back.
    """
    # The prompt must already be scrubbed. This is the last gate before the
    # bytes leave the process, and it applies to the system message too.
    scrub.assert_no_pii(prompt)
    if system:
        scrub.assert_no_pii(system)

    primary = model_for(purpose)
    key = cache_key(primary, purpose, prompt, system)
    started = time.perf_counter()

    cached = await _read_cache(session, key)
    if cached is not None:
        await _write_audit(
            session,
            user_id=user_id,
            purpose=purpose,
            model=primary,
            key=key,
            preview=prompt,
            latency_ms=int((time.perf_counter() - started) * 1000),
            cache_hit=True,
            success=True,
        )
        log.info("llm cache hit purpose=%s model=%s", purpose, primary)
        return cached["value"] if json_schema is None else cached

    if not settings.llm_configured:
        await _write_audit(
            session,
            user_id=user_id,
            purpose=purpose,
            model=primary,
            key=key,
            preview=prompt,
            latency_ms=int((time.perf_counter() - started) * 1000),
            cache_hit=False,
            success=False,
            error="no GROQ_API_KEY configured",
        )
        raise LLMUnavailable(
            "No GROQ_API_KEY configured; using the deterministic fallback."
        )

    # Attempt 1: primary model.
    # Attempt 2: primary again after a short backoff, if rate-limited.
    # Attempt 3: the small fast model, which has separate headroom.
    attempts: list[tuple[str, float]] = [
        (primary, 0.0),
        (primary, RATE_LIMIT_BACKOFF_S),
        (MODELS["fallback"], 0.0),
    ]

    last_error: Exception | None = None
    for index, (model, delay) in enumerate(attempts):
        if delay:
            await asyncio.sleep(delay)
        # gpt-oss is the only model here that honours strict schemas; if we have
        # fallen back to the small llama model, ask for plain JSON instead.
        schema = json_schema if model == primary else None
        try:
            text, in_tok, out_tok = await _call_groq(
                model=model,
                prompt=prompt,
                system=system,
                json_schema=schema,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            latency = int((time.perf_counter() - started) * 1000)

            if json_schema is not None:
                try:
                    payload: dict[str, Any] = json.loads(text)
                except json.JSONDecodeError as exc:
                    last_error = exc
                    log.warning("model %s returned unparsable JSON: %s", model, exc)
                    continue
            else:
                if not text.strip():
                    # An empty completion is a failure, not an answer, and it
                    # must never reach the cache: the key is derived from the
                    # prompt, so one transient empty response would be replayed
                    # for that prompt forever and the caller would fall back to
                    # a template every time, with no further calls to reveal it.
                    last_error = LLMUnavailable("model returned an empty completion")
                    continue
                payload = {"value": text.strip()}

            await _write_cache(session, key, model, purpose, payload)
            await _write_audit(
                session,
                user_id=user_id,
                purpose=purpose,
                model=model,
                key=key,
                preview=prompt,
                latency_ms=latency,
                cache_hit=False,
                success=True,
                input_tokens=in_tok,
                output_tokens=out_tok,
            )
            log.info(
                "llm ok purpose=%s model=%s attempt=%d %dms", purpose, model, index + 1, latency
            )
            return payload["value"] if json_schema is None else payload

        except Exception as exc:  # noqa: BLE001 - deliberately broad, see below
            last_error = exc
            rate_limited = _is_rate_limit(exc)
            log.warning(
                "llm attempt %d failed (model=%s, rate_limited=%s): %s",
                index + 1,
                model,
                rate_limited,
                exc,
            )
            # A non-rate-limit failure on the primary model still falls through
            # to the small model: a 500 or a timeout is just as worth retrying.
            continue

    latency = int((time.perf_counter() - started) * 1000)
    await _write_audit(
        session,
        user_id=user_id,
        purpose=purpose,
        model=primary,
        key=key,
        preview=prompt,
        latency_ms=latency,
        cache_hit=False,
        success=False,
        error=str(last_error) if last_error else "unknown failure",
    )
    raise LLMUnavailable(
        f"Groq unavailable after {len(attempts)} attempts: {last_error}"
    )
