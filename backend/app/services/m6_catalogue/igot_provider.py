"""The official-provider slot.

This is where a real iGOT Karmayogi integration would live. It is not
implemented, and this prototype makes no claim of having such access.
Selecting it raises immediately with an explanation.
"""

from __future__ import annotations

from app.core.errors import NotConfiguredError
from app.services.m6_catalogue.provider import (
    EnrollmentDTO,
    NominationDTO,
    OfferingDTO,
    ProviderInfo,
)

_MESSAGE = (
    "Official iGOT Karmayogi API access requires authorised credentials from the "
    "Capacity Building Commission. This prototype ships a mock provider conforming "
    "to the same interface."
)


class IgotProvider:
    """Every method raises. The class exists to show the seam is real."""

    name = "igot"

    def __init__(self) -> None:
        raise NotConfiguredError(_MESSAGE)

    async def list_courses(
        self, competency: str | None = None, level: int | None = None
    ) -> list[OfferingDTO]:
        raise NotConfiguredError(_MESSAGE)

    async def get_course(self, external_id: str) -> OfferingDTO:
        raise NotConfiguredError(_MESSAGE)

    async def enroll(self, user_ref: str, external_id: str) -> EnrollmentDTO:
        raise NotConfiguredError(_MESSAGE)

    async def nominate(
        self, user_ref: str, external_id: str, justification: str
    ) -> NominationDTO:
        raise NotConfiguredError(_MESSAGE)

    async def health(self) -> bool:
        return False

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            provider="igot",
            is_mock=False,
            description=_MESSAGE,
            reachable=False,
        )
