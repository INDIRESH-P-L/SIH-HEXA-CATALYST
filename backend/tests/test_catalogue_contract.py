"""M6 · contract tests for the catalogue seam.

These run against the ``CatalogueProvider`` Protocol rather than against any
one implementation. That is the point: the claim being made is not "we wrote a
mock", it is "there is a real interface, and a production provider that
satisfies it drops in without touching the rest of the application". A test
suite written against the interface is the artefact that supports the claim.

The mock service is driven in-process through ``httpx.ASGITransport``, so no
port is opened and no second process is needed, while the client under test is
the same HTTP client that talks to the real thing over a socket.
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

from app.core.errors import NotConfiguredError, NotFoundError
from app.services.m6_catalogue.provider import (
    CatalogueProvider,
    EnrollmentDTO,
    NominationDTO,
    OfferingDTO,
)

MOCK_SERVICE_DIR = Path(__file__).resolve().parents[2] / "mock-catalogue"


def _record_count(filename: str) -> int:
    """Read the expected count from the data itself.

    Hard-coding a total means the test fails whenever the catalogue grows,
    which teaches nothing. What matters is that the provider returns
    everything the service holds, and that both catalogues are merged.
    """
    import json

    return len(json.loads((MOCK_SERVICE_DIR / "data" / filename).read_text(encoding="utf-8")))


IGOT_COUNT = _record_count("igot_courses.json")
NSSTA_COUNT = _record_count("nssta_programmes.json")


@pytest.fixture(scope="module")
def mock_app():
    """The mock catalogue FastAPI application, imported directly."""
    sys.path.insert(0, str(MOCK_SERVICE_DIR))
    try:
        import main as mock_main  # type: ignore[import-not-found]
    finally:
        sys.path.pop(0)
    return mock_main.app


@pytest.fixture
def provider(mock_app, monkeypatch: pytest.MonkeyPatch) -> CatalogueProvider:
    """A MockProvider wired to the mock application in-process."""
    from app.services.m6_catalogue.mock_provider import MockProvider

    MockProvider.reset_breaker()
    return MockProvider(transport=httpx.ASGITransport(app=mock_app))


# ── the interface itself ─────────────────────────────────────────────────────


def test_mock_provider_satisfies_the_protocol(provider: CatalogueProvider) -> None:
    assert isinstance(provider, CatalogueProvider)


def test_the_official_provider_declares_the_same_interface() -> None:
    """IgotProvider must satisfy the Protocol even though it refuses to run."""
    from app.services.m6_catalogue.igot_provider import IgotProvider

    for method in ("list_courses", "get_course", "enroll", "nominate", "health", "info"):
        assert callable(getattr(IgotProvider, method))


def test_selecting_the_official_provider_says_why_it_cannot_run() -> None:
    """No claim of access is made anywhere, including in the failure message."""
    from app.services.m6_catalogue.igot_provider import IgotProvider

    with pytest.raises(NotConfiguredError) as excinfo:
        IgotProvider()

    message = str(excinfo.value)
    assert "authorised credentials" in message
    assert "Capacity Building Commission" in message


# ── list_courses ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_courses_returns_the_whole_catalogue(
    provider: CatalogueProvider,
) -> None:
    offerings = await provider.list_courses()
    assert len(offerings) == IGOT_COUNT + NSSTA_COUNT
    assert all(isinstance(o, OfferingDTO) for o in offerings)


@pytest.mark.asyncio
async def test_both_catalogues_are_merged(provider: CatalogueProvider) -> None:
    offerings = await provider.list_courses()
    assert sum(1 for o in offerings if o.source == "IGOT") == IGOT_COUNT
    assert sum(1 for o in offerings if o.source == "NSSTA") == NSSTA_COUNT
    assert IGOT_COUNT and NSSTA_COUNT, "both catalogues must contribute"


@pytest.mark.asyncio
async def test_every_offering_is_normalised_into_the_shared_shape(
    provider: CatalogueProvider,
) -> None:
    """Provider-specific field names never escape the seam."""
    for offering in await provider.list_courses():
        assert offering.external_id
        assert offering.title
        assert offering.competency_code == offering.competency_code.upper()
        assert 1 <= offering.proficiency_level <= 4, (
            f"{offering.external_id} sits outside the FRAC 4-point scale"
        )
        assert offering.duration_hours > 0
        assert offering.learning_format in (
            "SELF_PACED",
            "CLASSROOM",
            "BLENDED",
            "VIRTUAL_LAB",
        )
        assert isinstance(offering.prerequisites, list)


@pytest.mark.asyncio
async def test_descriptions_are_substantial_enough_to_embed(
    provider: CatalogueProvider,
) -> None:
    """Semantic matching is computed from these, so filler would break it."""
    for offering in await provider.list_courses():
        assert len(offering.description) >= 120
        assert offering.embedding_text.startswith(offering.title)


@pytest.mark.asyncio
async def test_filtering_by_competency(provider: CatalogueProvider) -> None:
    offerings = await provider.list_courses(competency="SQL")
    assert offerings
    assert {o.competency_code for o in offerings} == {"SQL"}


@pytest.mark.asyncio
async def test_the_catalogue_covers_every_seeded_competency(
    provider: CatalogueProvider,
) -> None:
    """Every demo gap must have candidates, or the recommender looks broken."""
    from app.seed.competencies_data import CODES

    covered = {o.competency_code for o in await provider.list_courses()}
    missing = CODES - covered
    assert not missing, f"no offering for {sorted(missing)}"


# ── get_course ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_course_by_external_id(provider: CatalogueProvider) -> None:
    offering = await provider.get_course("IGOT-SQL-101")
    assert offering.title == "SQL Fundamentals for Statistical Analysis"
    assert offering.source == "IGOT"


@pytest.mark.asyncio
async def test_get_course_routes_nssta_ids_to_the_academy_catalogue(
    provider: CatalogueProvider,
) -> None:
    offering = await provider.get_course("NSSTA-NAS-401")
    assert offering.source == "NSSTA"
    assert offering.session_start is not None
    assert offering.seats is not None


@pytest.mark.asyncio
async def test_an_unknown_id_is_not_found_rather_than_an_outage(
    provider: CatalogueProvider,
) -> None:
    with pytest.raises(NotFoundError):
        await provider.get_course("IGOT-DOES-NOT-EXIST")


# ── the two enrolment paths ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_igot_courses_are_self_enrolled(provider: CatalogueProvider) -> None:
    result = await provider.enroll("user-ref-1", "IGOT-SQL-101")
    assert isinstance(result, EnrollmentDTO)
    assert result.status == "ENROLLED"
    assert result.external_ref.startswith("ENR-")


@pytest.mark.asyncio
async def test_nssta_programmes_are_nominated_for_not_enrolled(
    provider: CatalogueProvider,
) -> None:
    """An officer requests; a controlling authority nominates; the academy confirms.

    Only the first step is modelled, and the returned status says so.
    """
    result = await provider.nominate(
        "user-ref-1", "NSSTA-NAS-401", "Role requires level 4 national accounts."
    )
    assert isinstance(result, NominationDTO)
    assert result.status == "REQUESTED"
    assert result.external_ref.startswith("NOM-")
    assert result.nominating_authority


@pytest.mark.asyncio
async def test_the_user_reference_sent_upstream_is_opaque(
    provider: CatalogueProvider,
) -> None:
    """No name or employee code crosses the seam."""
    result = await provider.enroll("3f2504e0-4f89-11d3-9a0c-0305e82c3301", "IGOT-PY-101")
    assert result.status == "ENROLLED"


# ── honesty ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_the_provider_declares_itself_a_mock(provider: CatalogueProvider) -> None:
    """The interface a judge can call to check the claim themselves."""
    info = provider.info()
    assert info.is_mock is True
    assert info.provider == "mock"
    assert "authorised API credentials" in info.description


@pytest.mark.asyncio
async def test_health_reports_reachability(provider: CatalogueProvider) -> None:
    assert await provider.health() is True


# ── the circuit breaker ──────────────────────────────────────────────────────


def test_the_breaker_opens_after_repeated_failures() -> None:
    """What MOCK_FLAKY=true exists to demonstrate."""
    from app.services.m6_catalogue.breaker import CircuitBreaker

    breaker = CircuitBreaker(name="test", threshold=3, cooldown_s=60)
    assert breaker.is_open is False

    breaker.record_failure()
    breaker.record_failure()
    assert breaker.is_open is False, "should tolerate a transient blip"

    breaker.record_failure()
    assert breaker.is_open is True
    assert breaker.state == "open"


def test_a_success_closes_the_breaker() -> None:
    from app.services.m6_catalogue.breaker import CircuitBreaker

    breaker = CircuitBreaker(name="test", threshold=2, cooldown_s=60)
    breaker.record_failure()
    breaker.record_success()
    breaker.record_failure()
    assert breaker.is_open is False, "the counter must reset on success"


def test_the_breaker_half_opens_after_the_cooldown() -> None:
    from app.services.m6_catalogue.breaker import CircuitBreaker

    breaker = CircuitBreaker(name="test", threshold=1, cooldown_s=0)
    breaker.record_failure()
    assert breaker.is_open is False, "a zero cooldown admits a trial call immediately"
