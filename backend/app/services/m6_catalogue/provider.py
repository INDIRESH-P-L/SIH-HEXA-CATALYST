"""M6 · the catalogue seam.

This prototype does not have access to the official iGOT Karmayogi or NSSTA
APIs. Obtaining it requires authorised credentials from the Capacity Building
Commission (iGOT) and from the academy (NSSTA).

What exists instead is this interface, plus a mock service that implements it
faithfully — same request shapes, same envelope, same auth header, same
latency, same failure modes. The contract tests in ``tests/test_catalogue_contract.py``
run against this Protocol rather than against either implementation, which is
what makes the seam verifiable rather than merely asserted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Protocol, runtime_checkable

CatalogueSource = Literal["IGOT", "NSSTA"]
LearningFormat = Literal["SELF_PACED", "CLASSROOM", "BLENDED", "VIRTUAL_LAB"]


@dataclass(frozen=True)
class OfferingDTO:
    """A course or programme as the catalogue describes it.

    Normalised away from any one provider's field names, so a real iGOT
    integration would map into this shape without the rest of the application
    changing.
    """

    external_id: str
    source: CatalogueSource
    title: str
    provider: str
    competency_code: str
    proficiency_level: int
    duration_hours: int
    description: str
    learning_format: LearningFormat
    prerequisites: list[str] = field(default_factory=list)
    course_url: str | None = None
    status: str = "ACTIVE"
    # NSSTA dated programmes only.
    session_start: date | None = None
    seats: int | None = None
    nominating_authority: str | None = None
    venue: str | None = None

    @property
    def embedding_text(self) -> str:
        """The text the semantic index is built from.

        Title plus description, because a title alone is too short to place a
        course reliably in embedding space.
        """
        return f"{self.title}. {self.description}"


@dataclass(frozen=True)
class EnrollmentDTO:
    """Result of a self-enrolment (the iGOT path)."""

    external_ref: str
    external_id: str
    status: str


@dataclass(frozen=True)
class NominationDTO:
    """Result of a nomination request (the NSSTA path).

    A nomination is a request, not an enrolment. The officer asks, a
    controlling authority nominates, and the academy confirms. This prototype
    models only the first step and says so.
    """

    external_ref: str
    external_id: str
    status: str
    nominating_authority: str | None = None


@dataclass(frozen=True)
class ProviderInfo:
    """What the frontend renders as a visible badge on catalogue data."""

    provider: str
    is_mock: bool
    description: str
    base_url: str | None = None
    record_count: int | None = None
    reachable: bool | None = None


@runtime_checkable
class CatalogueProvider(Protocol):
    """Read offerings, enrol, and request nominations."""

    name: str

    async def list_courses(
        self, competency: str | None = None, level: int | None = None
    ) -> list[OfferingDTO]:
        ...

    async def get_course(self, external_id: str) -> OfferingDTO:
        ...

    async def enroll(self, user_ref: str, external_id: str) -> EnrollmentDTO:
        ...

    async def nominate(
        self, user_ref: str, external_id: str, justification: str
    ) -> NominationDTO:
        ...

    async def health(self) -> bool:
        ...

    def info(self) -> ProviderInfo:
        ...


def get_catalogue_provider() -> CatalogueProvider:
    """Resolve the configured catalogue provider."""
    from app.core.config import settings

    if settings.CATALOGUE_PROVIDER == "igot":
        from app.services.m6_catalogue.igot_provider import IgotProvider

        return IgotProvider()

    from app.services.m6_catalogue.mock_provider import MockProvider

    return MockProvider()
