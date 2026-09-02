"""Catalogue provider backed by the mock service on port 8001.

The mock is a genuinely separate process, reached over HTTP with an API key,
so this client has to deal with real network conditions: timeouts, latency,
and the 503s the mock emits when MOCK_FLAKY=true. That is the point — a client
that only ever called an in-process function would prove nothing about the seam.

The transport is injectable so contract tests can run the same client against
the mock application in-process, with no port and no sockets.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.core.config import settings
from app.core.errors import NotFoundError, UpstreamUnavailable
from app.core.logging import get_logger
from app.services.m6_catalogue.breaker import CircuitBreaker
from app.services.m6_catalogue.provider import (
    EnrollmentDTO,
    NominationDTO,
    OfferingDTO,
    ProviderInfo,
)

log = get_logger(__name__)

#: Module-level so the breaker state survives across requests within a process.
_breaker = CircuitBreaker(
    name="catalogue",
    threshold=settings.CATALOGUE_BREAKER_THRESHOLD,
    cooldown_s=settings.CATALOGUE_BREAKER_COOLDOWN_S,
)


def _to_offering(raw: dict[str, Any], source: str) -> OfferingDTO:
    """Normalise a catalogue record into the shared DTO."""
    session_start = raw.get("session_start")
    parsed_start: date | None = None
    if session_start:
        try:
            parsed_start = date.fromisoformat(str(session_start))
        except ValueError:
            parsed_start = None

    return OfferingDTO(
        external_id=str(raw["course_id"]),
        source="NSSTA" if source == "NSSTA" else "IGOT",
        title=str(raw["title"]),
        provider=str(raw["provider"]),
        competency_code=str(raw["competency"]),
        proficiency_level=int(raw["proficiency_level"]),
        duration_hours=int(raw["duration"]),
        description=str(raw["description"]),
        learning_format=str(raw["learning_format"]),  # type: ignore[arg-type]
        prerequisites=list(raw.get("prerequisites") or []),
        course_url=raw.get("course_url"),
        status=str(raw.get("status", "ACTIVE")),
        session_start=parsed_start,
        seats=raw.get("seats"),
        nominating_authority=raw.get("nominating_authority"),
        venue=raw.get("venue"),
    )


class MockProvider:
    """HTTP client for the mock iGOT / NSSTA service."""

    name = "mock"

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._base = settings.MOCK_CATALOGUE_URL.rstrip("/")
        self._transport = transport
        self._timeout = httpx.Timeout(settings.CATALOGUE_TIMEOUT_S)

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base,
            timeout=self._timeout,
            transport=self._transport,
            headers={"X-API-Key": settings.MOCK_API_KEY},
        )

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Issue one request, updating breaker state on the outcome."""
        if _breaker.is_open:
            raise UpstreamUnavailable(
                "The catalogue service is unavailable; serving the local mirror."
            )
        try:
            async with self._client() as client:
                resp = await client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            _breaker.record_failure()
            raise UpstreamUnavailable(f"Catalogue service unreachable: {exc}") from exc

        if resp.status_code == 404:
            # A missing record is a valid answer, not an outage.
            _breaker.record_success()
            raise NotFoundError("No such offering in the catalogue.")
        if resp.status_code >= 500:
            _breaker.record_failure()
            raise UpstreamUnavailable(
                f"Catalogue service returned {resp.status_code}."
            )
        if resp.status_code >= 400:
            _breaker.record_success()
            raise UpstreamUnavailable(
                f"Catalogue service rejected the request ({resp.status_code}). "
                "Check MOCK_API_KEY."
            )

        _breaker.record_success()
        return resp.json()

    @staticmethod
    def _content(body: dict[str, Any]) -> list[dict[str, Any]]:
        """Unwrap the Sunbird-style envelope the service returns."""
        return list(body.get("result", {}).get("content", []))

    async def list_courses(
        self, competency: str | None = None, level: int | None = None
    ) -> list[OfferingDTO]:
        """Both catalogues, merged. Either one failing fails the call."""
        params: dict[str, Any] = {"limit": 200}
        if competency:
            params["competency"] = competency
        if level is not None:
            params["level"] = level

        igot = await self._request("GET", "/igot/v1/courses", params=params)
        nssta = await self._request("GET", "/nssta/v1/programmes", params=params)

        offerings = [_to_offering(r, "IGOT") for r in self._content(igot)]
        offerings += [_to_offering(r, "NSSTA") for r in self._content(nssta)]
        return offerings

    async def get_course(self, external_id: str) -> OfferingDTO:
        """Look the id up in whichever catalogue owns its prefix."""
        if external_id.upper().startswith("NSSTA"):
            body = await self._request("GET", f"/nssta/v1/programmes/{external_id}")
            return _to_offering(body["result"], "NSSTA")
        body = await self._request("GET", f"/igot/v1/courses/{external_id}")
        return _to_offering(body["result"], "IGOT")

    async def enroll(self, user_ref: str, external_id: str) -> EnrollmentDTO:
        """The iGOT path: self-enrolment, immediate."""
        body = await self._request(
            "POST",
            "/igot/v1/enrollments",
            json={"user_ref": user_ref, "course_id": external_id},
        )
        result = body["result"]
        return EnrollmentDTO(
            external_ref=str(result["enrollment_id"]),
            external_id=external_id,
            status=str(result.get("status", "ENROLLED")),
        )

    async def nominate(
        self, user_ref: str, external_id: str, justification: str
    ) -> NominationDTO:
        """The NSSTA path: a request that a controlling authority must act on."""
        body = await self._request(
            "POST",
            "/nssta/v1/nominations",
            json={
                "user_ref": user_ref,
                "programme_id": external_id,
                "justification": justification,
            },
        )
        result = body["result"]
        return NominationDTO(
            external_ref=str(result["nomination_id"]),
            external_id=external_id,
            status=str(result.get("status", "REQUESTED")),
            nominating_authority=result.get("nominating_authority"),
        )

    async def health(self) -> bool:
        try:
            async with self._client() as client:
                resp = await client.get("/meta/health")
            ok = resp.status_code == 200
            _breaker.record_success() if ok else _breaker.record_failure()
            return ok
        except httpx.HTTPError:
            _breaker.record_failure()
            return False

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            provider="mock",
            is_mock=True,
            description=(
                "Mock catalogue service conforming to a documented interface. "
                "Production deployment requires authorised API credentials from "
                "the Capacity Building Commission (iGOT) and NSSTA."
            ),
            base_url=self._base,
        )

    @staticmethod
    def breaker_state() -> str:
        return _breaker.state

    @staticmethod
    def reset_breaker() -> None:
        _breaker.reset()
