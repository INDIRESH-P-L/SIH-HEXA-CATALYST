"""The single Groq chokepoint.

Exercised against a fake client and an in-memory session stub, so these run
with no network, no API key and no database. What matters is the control flow:
cache before call, retry then fall back, audit on every path, and the PII
assertion before anything leaves.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from app.ai import llm_client
from app.core.config import settings
from app.core.errors import LLMUnavailable, PIILeakError


# ── stubs ────────────────────────────────────────────────────────────────────


class FakeSession:
    """Enough of AsyncSession for llm_client: add / flush / scalar / get."""

    def __init__(self, cached: dict[str, Any] | None = None) -> None:
        self.added: list[Any] = []
        self.cached = cached
        self.flushes = 0

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        self.flushes += 1

    async def scalar(self, _stmt: Any) -> Any:
        if self.cached is None:
            return None

        class Row:
            response = self.cached

        return Row()

    async def get(self, _model: Any, _key: Any) -> Any:
        return None

    @property
    def audits(self) -> list[Any]:
        from app.models.ai import LLMAudit

        return [a for a in self.added if isinstance(a, LLMAudit)]

    @property
    def caches(self) -> list[Any]:
        from app.models.ai import LLMCache

        return [c for c in self.added if isinstance(c, LLMCache)]


class FakeRateLimit(Exception):
    """Stands in for groq.RateLimitError, matched by class name."""

    status_code = 429


FakeRateLimit.__name__ = "RateLimitError"


class FakeCompletions:
    def __init__(self, script: list[Any]) -> None:
        self.script = list(script)
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        outcome = self.script.pop(0) if self.script else "{}"
        if isinstance(outcome, Exception):
            raise outcome

        class Message:
            content = outcome

        class Choice:
            message = Message()

        class Usage:
            prompt_tokens = 100
            completion_tokens = 50

        class Response:
            choices = [Choice()]
            usage = Usage()

        return Response()


class FakeClient:
    def __init__(self, script: list[Any]) -> None:
        self.chat = type("Chat", (), {"completions": FakeCompletions(script)})()

    @property
    def calls(self) -> list[dict[str, Any]]:
        return self.chat.completions.calls  # type: ignore[attr-defined]


@pytest.fixture
def with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(settings, "LLM_ENABLED", True)
    monkeypatch.setattr(settings, "LLM_CACHE_ENABLED", True)
    llm_client.reset_client()


def install(monkeypatch: pytest.MonkeyPatch, script: list[Any]) -> FakeClient:
    client = FakeClient(script)
    monkeypatch.setattr(llm_client, "get_client", lambda: client)
    return client


# ── cache key ────────────────────────────────────────────────────────────────


def test_cache_key_is_stable_and_input_sensitive() -> None:
    a = llm_client.cache_key("m", "explanation", "prompt", None)
    assert a == llm_client.cache_key("m", "explanation", "prompt", None)
    assert a != llm_client.cache_key("m", "explanation", "other prompt", None)
    assert a != llm_client.cache_key("m", "feedback", "prompt", None)
    assert a != llm_client.cache_key("other", "explanation", "prompt", None)
    assert a != llm_client.cache_key("m", "explanation", "prompt", "system")


# ── model routing ────────────────────────────────────────────────────────────


def test_mcq_generation_routes_to_the_structured_output_model() -> None:
    """Strict JSON schema works on GPT-OSS, not on llama-3.3-70b."""
    assert llm_client.model_for("mcq_generation") == settings.MODEL_MCQ
    assert llm_client.model_for("explanation") == settings.MODEL_TEXT
    assert llm_client.model_for("feedback") == settings.MODEL_TEXT


# ── cache hit ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_a_cache_hit_skips_the_provider_entirely(
    monkeypatch: pytest.MonkeyPatch, with_key: None
) -> None:
    client = install(monkeypatch, ["should not be reached"])
    session = FakeSession(cached={"value": "cached explanation"})

    result = await llm_client.complete(
        session=session, purpose="explanation", prompt="hello"
    )

    assert result == "cached explanation"
    assert client.calls == []


@pytest.mark.asyncio
async def test_a_cache_hit_is_still_audited(
    monkeypatch: pytest.MonkeyPatch, with_key: None
) -> None:
    """The audit records what was asked, not only what was billed."""
    install(monkeypatch, [])
    session = FakeSession(cached={"value": "cached"})

    await llm_client.complete(session=session, purpose="explanation", prompt="hello")

    assert len(session.audits) == 1
    assert session.audits[0].cache_hit is True
    assert session.audits[0].success is True


# ── happy path ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_a_successful_call_is_cached_and_audited(
    monkeypatch: pytest.MonkeyPatch, with_key: None
) -> None:
    install(monkeypatch, ["a written explanation"])
    session = FakeSession()

    result = await llm_client.complete(
        session=session, purpose="explanation", prompt="hello"
    )

    assert result == "a written explanation"
    assert len(session.caches) == 1
    assert len(session.audits) == 1
    assert session.audits[0].cache_hit is False
    assert session.audits[0].input_tokens == 100


@pytest.mark.asyncio
async def test_a_json_schema_call_returns_the_parsed_object(
    monkeypatch: pytest.MonkeyPatch, with_key: None
) -> None:
    payload = {"questions": [{"question_text": "Q?"}]}
    client = install(monkeypatch, [json.dumps(payload)])
    session = FakeSession()

    result = await llm_client.complete(
        session=session,
        purpose="mcq_generation",
        prompt="generate",
        json_schema={"name": "mcq_batch", "schema": {"type": "object"}},
    )

    assert result == payload
    sent = client.calls[0]["response_format"]
    assert sent["type"] == "json_schema"
    assert sent["json_schema"]["strict"] is True


# ── retry and fallback ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_a_rate_limit_is_retried_then_falls_back_to_the_small_model(
    monkeypatch: pytest.MonkeyPatch, with_key: None
) -> None:
    monkeypatch.setattr(llm_client, "RATE_LIMIT_BACKOFF_S", 0)
    client = install(
        monkeypatch, [FakeRateLimit("429"), FakeRateLimit("429"), "recovered"]
    )
    session = FakeSession()

    result = await llm_client.complete(
        session=session, purpose="explanation", prompt="hello"
    )

    assert result == "recovered"
    assert len(client.calls) == 3
    assert client.calls[0]["model"] == settings.MODEL_TEXT
    assert client.calls[2]["model"] == settings.MODEL_FALLBACK


@pytest.mark.asyncio
async def test_total_failure_raises_llm_unavailable_and_is_audited(
    monkeypatch: pytest.MonkeyPatch, with_key: None
) -> None:
    monkeypatch.setattr(llm_client, "RATE_LIMIT_BACKOFF_S", 0)
    install(monkeypatch, [RuntimeError("boom")] * 3)
    session = FakeSession()

    with pytest.raises(LLMUnavailable):
        await llm_client.complete(session=session, purpose="explanation", prompt="hi")

    assert session.audits[-1].success is False
    assert "boom" in (session.audits[-1].error or "")


@pytest.mark.asyncio
async def test_unparsable_json_is_treated_as_a_failed_attempt(
    monkeypatch: pytest.MonkeyPatch, with_key: None
) -> None:
    monkeypatch.setattr(llm_client, "RATE_LIMIT_BACKOFF_S", 0)
    install(monkeypatch, ["not json", "not json either", '{"questions": []}'])
    session = FakeSession()

    result = await llm_client.complete(
        session=session,
        purpose="mcq_generation",
        prompt="generate",
        json_schema={"name": "mcq_batch", "schema": {"type": "object"}},
    )
    assert result == {"questions": []}


# ── no key configured ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_missing_api_key_raises_immediately_without_calling_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The offline path every caller falls back from."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    llm_client.reset_client()
    session = FakeSession()

    with pytest.raises(LLMUnavailable):
        await llm_client.complete(session=session, purpose="explanation", prompt="hi")

    assert session.audits[-1].success is False


@pytest.mark.asyncio
async def test_the_cache_still_serves_when_no_key_is_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """This is what makes the demonstration work with the network disconnected."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "LLM_CACHE_ENABLED", True)
    llm_client.reset_client()
    session = FakeSession(cached={"value": "pre-warmed"})

    result = await llm_client.complete(
        session=session, purpose="explanation", prompt="hi"
    )
    assert result == "pre-warmed"


# ── the PII gate ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_a_prompt_containing_pii_never_reaches_the_provider(
    monkeypatch: pytest.MonkeyPatch, with_key: None
) -> None:
    client = install(monkeypatch, ["should not be reached"])
    session = FakeSession()

    with pytest.raises(PIILeakError):
        await llm_client.complete(
            session=session,
            purpose="explanation",
            prompt="Write advice for priya.sharma@mospi.gov.in",
        )

    assert client.calls == []


@pytest.mark.asyncio
async def test_the_system_message_is_checked_too(
    monkeypatch: pytest.MonkeyPatch, with_key: None
) -> None:
    client = install(monkeypatch, ["should not be reached"])
    session = FakeSession()

    with pytest.raises(PIILeakError):
        await llm_client.complete(
            session=session,
            purpose="explanation",
            prompt="clean prompt",
            system="You advise officer MOSPI/2021/0847",
        )

    assert client.calls == []
