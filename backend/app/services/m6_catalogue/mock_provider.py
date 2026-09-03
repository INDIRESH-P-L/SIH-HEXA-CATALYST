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
    """Normalise a catalogue record into the shared DTO.
    Supports both D:\igot REST API course objects and legacy mock stubs.
    """
    session_start = raw.get("session_start")
    parsed_start: date | None = None
    if session_start:
        try:
            parsed_start = date.fromisoformat(str(session_start)[:10])
        except ValueError:
            parsed_start = None

    external_id = str(raw.get("external_id") or raw.get("course_id") or raw.get("id"))
    raw_source = str(raw.get("source") or source or "IGOT").upper()
    
    # Competency mapping
    comp_code = raw.get("competency") or raw.get("competency_code")
    if not comp_code and raw.get("competencies") and isinstance(raw["competencies"], list):
        first_comp = raw["competencies"][0]
        if isinstance(first_comp, dict):
            comp_code = first_comp.get("competency_code") or first_comp.get("code")
    if not comp_code:
        comp_code = "GENERAL"

    # Level mapping
    level = raw.get("proficiency_level") or raw.get("level")
    if not level and raw.get("competencies") and isinstance(raw["competencies"], list):
        first_comp = raw["competencies"][0]
        if isinstance(first_comp, dict):
            level = first_comp.get("proficiency_level") or first_comp.get("level")
    proficiency_level = int(level) if level else 1

    duration = raw.get("duration_hours") or raw.get("duration") or 10
    learning_format = raw.get("learning_mode") or raw.get("learning_format") or "SELF_PACED"
    provider = raw.get("provider_name") or raw.get("provider") or "iGOT Karmayogi — CBC"

    course_url = raw.get("course_url")
    if not course_url:
        course_url = f"http://localhost:5174/course/{external_id}"

    return OfferingDTO(
        external_id=external_id,
        source="NSSTA" if raw_source == "NSSTA" else "IGOT",
        title=str(raw.get("title", "")),
        provider=str(provider),
        competency_code=str(comp_code),
        proficiency_level=proficiency_level,
        duration_hours=int(duration),
        description=str(raw.get("description", "")),
        learning_format=str(learning_format),  # type: ignore[arg-type]
        prerequisites=list(raw.get("prerequisites") or []),
        course_url=course_url,
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
        """Fetch all courses from mock iGOT (D:\igot) or fallback to legacy stubs."""
        params: dict[str, Any] = {"limit": 200}
        if competency:
            params["competency"] = competency
        if level is not None:
            params["level"] = level

        # 1. Primary path: D:\igot API (GET /api/v1/courses)
        try:
            body = await self._request("GET", "/api/v1/courses", params=params)
            courses_data = body.get("data")
            if isinstance(courses_data, list) and len(courses_data) > 0:
                return [
                    _to_offering(r, r.get("source", "IGOT"))
                    for r in courses_data
                ]
        except (NotFoundError, UpstreamUnavailable) as exc:
            # If not found or service rejected path, fall through to legacy mock endpoints
            if isinstance(exc, UpstreamUnavailable) and "unreachable" in str(exc):
                raise

        # 2. Legacy fallback: /igot/v1/courses and /nssta/v1/programmes
        igot = await self._request("GET", "/igot/v1/courses", params=params)
        nssta = await self._request("GET", "/nssta/v1/programmes", params=params)

        offerings = [_to_offering(r, "IGOT") for r in self._content(igot)]
        offerings += [_to_offering(r, "NSSTA") for r in self._content(nssta)]
        return offerings

    async def get_course(self, external_id: str) -> OfferingDTO:
        """Fetch a single course by ID or external ID."""
        # 1. Primary path: D:\igot API (GET /api/v1/courses/{external_id})
        try:
            body = await self._request("GET", f"/api/v1/courses/{external_id}")
            course_data = body.get("data")
            if isinstance(course_data, dict):
                return _to_offering(course_data, course_data.get("source", "IGOT"))
        except NotFoundError:
            pass

        # 2. Legacy fallback
        if external_id.upper().startswith("NSSTA"):
            body = await self._request("GET", f"/nssta/v1/programmes/{external_id}")
            return _to_offering(body["result"], "NSSTA")
        body = await self._request("GET", f"/igot/v1/courses/{external_id}")
        return _to_offering(body["result"], "IGOT")

    async def enroll(self, user_ref: str, external_id: str) -> EnrollmentDTO:
        """The iGOT path: self-enrolment in mock iGOT platform."""
        # 1. Primary path: D:\igot API (POST /api/v1/courses/{external_id}/enroll)
        try:
            body = await self._request(
                "POST",
                f"/api/v1/courses/{external_id}/enroll",
                json={"user_ref": user_ref},
            )
            data = body.get("data") or body.get("result") or {}
            ext_ref = data.get("external_ref") or data.get("enrollment_id")
            if ext_ref:
                return EnrollmentDTO(
                    external_ref=str(ext_ref),
                    external_id=external_id,
                    status=str(data.get("status", "ENROLLED")),
                )
        except NotFoundError:
            pass

        # 2. Legacy fallback: POST /igot/v1/enrollments
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
        # In D:\igot, all courses can be registered/enrolled
        try:
            body = await self._request(
                "POST",
                f"/api/v1/courses/{external_id}/enroll",
                json={"user_ref": user_ref},
            )
            data = body.get("data") or body.get("result") or {}
            ext_ref = data.get("external_ref") or data.get("enrollment_id")
            if ext_ref:
                return NominationDTO(
                    external_ref=str(ext_ref),
                    external_id=external_id,
                    status="NOMINATION_REQUESTED",
                    nominating_authority="NSSTA Training Academy",
                )
        except NotFoundError:
            pass

        # Legacy fallback
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
                resp = await client.get("/health")
                if resp.status_code != 200:
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
