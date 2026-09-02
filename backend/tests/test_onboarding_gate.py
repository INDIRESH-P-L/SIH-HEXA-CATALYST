"""The onboarding gate — is this officer new, and who is asked at all.

Re-running the onboarding wizard is destructive: it appends a self-declaration
for every competency at the cluster default, and ``user_competency`` reads the
latest row per (user, competency), so a second pass would supersede seeded
baselines and real assessment evidence with flat guesses at confidence 0.25.

What stops that is the answer to one question — "does this officer have any
evidence on file?" — asked of the ledger rather than of the browser. These are
the cases that answer has to survive.
"""

from __future__ import annotations

import uuid

import pytest

from app.schemas.auth import MeResponse
from app.schemas.profile import ProfileRead
from app.services.m2_framework import has_evidence_on_file


class FakeSession:
    """Just enough AsyncSession to answer one ``scalar`` call.

    The query itself is exercised against a live database by the end-to-end
    verification; what is worth pinning here is the branch it drives, because
    an inverted answer silently re-flattens an officer's whole record.
    """

    def __init__(self, result: object) -> None:
        self._result = result
        self.calls = 0

    async def scalar(self, _statement: object) -> object:
        self.calls += 1
        return self._result


# ── the ledger is the completion record ──────────────────────────────────────


@pytest.mark.asyncio
async def test_an_officer_with_evidence_is_onboarded() -> None:
    session = FakeSession(uuid.uuid4())
    assert await has_evidence_on_file(session, uuid.uuid4()) is True  # type: ignore[arg-type]
    assert session.calls == 1


@pytest.mark.asyncio
async def test_an_empty_ledger_means_a_new_officer() -> None:
    session = FakeSession(None)
    assert await has_evidence_on_file(session, uuid.uuid4()) is False  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_the_answer_is_a_bool_not_the_row() -> None:
    """The route guard compares against a boolean; a UUID would be truthy but
    would also leak an evidence id into the session payload."""
    result = await has_evidence_on_file(FakeSession(uuid.uuid4()), uuid.uuid4())  # type: ignore[arg-type]
    assert isinstance(result, bool)


# ── the flag survives serialisation ──────────────────────────────────────────


def _me(**overrides: object) -> MeResponse:
    payload: dict[str, object] = {
        "id": uuid.uuid4(),
        "email": "officer@mospi.gov.in",
        "roles": ["employee"],
        "profile": ProfileRead(id=uuid.uuid4(), full_name="Test Officer"),
        "auth_mode": "local",
    }
    payload.update(overrides)
    return MeResponse(**payload)  # type: ignore[arg-type]


def test_the_session_payload_carries_the_flag() -> None:
    assert _me(onboarded=False).model_dump()["onboarded"] is False
    assert _me(onboarded=True).model_dump()["onboarded"] is True


def test_the_default_does_not_send_an_officer_back_into_the_wizard() -> None:
    """If the field is ever missing, the safe reading is "already onboarded".

    Defaulting the other way would route an established officer into a wizard
    that overwrites their record — the failure this whole gate exists to stop.
    """
    assert _me().onboarded is True
