"""Mock iGOT Karmayogi / NSSTA catalogue service.

THIS IS NOT AN OFFICIAL API AND IT IS NOT CONNECTED TO ONE.

It is a stand-in that implements the interface the platform expects, so the
integration seam can be built, tested and demonstrated without claiming access
we do not have. Obtaining real access requires authorised credentials from the
Capacity Building Commission (iGOT) and from NSSTA.

It runs as a genuinely separate process, not an in-process module::

    cd mock-catalogue && uvicorn main:app --port 8001

Being a separate process is the point. The backend has to deal with a real
network hop, real latency, an API key, and real failures — none of which an
in-process function call would exercise.

Behaviour that keeps it honest:
  * requires an X-API-Key header and returns 401 without it;
  * stamps X-Mock-Source: mock on every response;
  * adds 150-400ms of artificial latency;
  * returns a Sunbird-shaped envelope, since iGOT is built on Sunbird;
  * returns 503 on roughly 2% of requests when MOCK_FLAKY=true, so the
    backend's circuit breaker and mirror fallback can be demonstrated.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

DATA_DIR = Path(__file__).parent / "data"
API_KEY = os.getenv("MOCK_API_KEY", "sih-2026-mock-key")
FLAKY = os.getenv("MOCK_FLAKY", "false").lower() in {"1", "true", "yes"}
FLAKY_RATE = float(os.getenv("MOCK_FLAKY_RATE", "0.02"))
LATENCY_MIN = float(os.getenv("MOCK_LATENCY_MIN", "0.15"))
LATENCY_MAX = float(os.getenv("MOCK_LATENCY_MAX", "0.40"))


def _load(filename: str) -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))


IGOT_COURSES: list[dict[str, Any]] = _load("igot_courses.json")
NSSTA_PROGRAMMES: list[dict[str, Any]] = _load("nssta_programmes.json")

#: In-memory only. Restarting the service clears enrolments, which is correct
#: for a mock: the platform's own database is the record of truth.
ENROLLMENTS: dict[str, dict[str, Any]] = {}
NOMINATIONS: dict[str, dict[str, Any]] = {}

app = FastAPI(
    title="Mock iGOT Karmayogi / NSSTA Catalogue",
    version="0.1.0",
    description=(
        "A mock service conforming to a documented catalogue interface. "
        "It is not an official API and is not connected to one. Production "
        "deployment requires authorised API credentials from the Capacity "
        "Building Commission (iGOT) and NSSTA."
    ),
)


# ── Request / response models ────────────────────────────────────────────────


class EnrollmentRequest(BaseModel):
    user_ref: str = Field(description="Opaque caller-side reference. Not a name.")
    course_id: str


class NominationRequest(BaseModel):
    user_ref: str
    programme_id: str
    justification: str = ""


# ── Cross-cutting behaviour ──────────────────────────────────────────────────


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Reject anything without the shared key, as a real gateway would."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key.")


@app.middleware("http")
async def mock_behaviour(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Artificial latency, occasional outages, and an honesty header."""
    await asyncio.sleep(random.uniform(LATENCY_MIN, LATENCY_MAX))

    if FLAKY and request.url.path != "/meta/health" and random.random() < FLAKY_RATE:
        resp: Any = JSONResponse(
            status_code=503,
            content={
                "responseCode": "SERVICE_UNAVAILABLE",
                "params": {"errmsg": "Simulated upstream outage (MOCK_FLAKY=true)."},
            },
        )
    else:
        resp = await call_next(request)

    resp.headers["X-Mock-Source"] = "mock"
    resp.headers["X-Mock-Notice"] = "Not an official iGOT or NSSTA API."
    return resp


def envelope(content: Any, count: int | None = None) -> dict[str, Any]:
    """The Sunbird-ish response shape iGOT clients expect."""
    body: dict[str, Any] = {
        "id": "api.catalogue.read",
        "ver": "v1",
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "params": {"status": "successful"},
        "responseCode": "OK",
        "result": content if count is None else {"content": content, "count": count},
    }
    return body


def _filter(
    records: list[dict[str, Any]],
    competency: str | None,
    level: int | None,
) -> list[dict[str, Any]]:
    out = records
    if competency:
        wanted = competency.strip().upper()
        out = [r for r in out if str(r["competency"]).upper() == wanted]
    if level is not None:
        out = [r for r in out if int(r["proficiency_level"]) == level]
    return out


# ── iGOT catalogue: self-paced courses, self-enrolled ────────────────────────


@app.get("/igot/v1/courses", dependencies=[Depends(require_api_key)], tags=["igot"])
async def list_igot_courses(
    competency: str | None = None,
    level: int | None = Query(default=None, ge=1, le=5),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    rows = _filter(IGOT_COURSES, competency, level)
    page = rows[offset : offset + limit]
    return envelope(page, count=len(rows))


@app.get(
    "/igot/v1/courses/{course_id}", dependencies=[Depends(require_api_key)], tags=["igot"]
)
async def get_igot_course(course_id: str) -> dict[str, Any]:
    for row in IGOT_COURSES:
        if row["course_id"] == course_id:
            return envelope(row)
    raise HTTPException(status_code=404, detail=f"No course {course_id}.")


@app.post(
    "/igot/v1/enrollments",
    dependencies=[Depends(require_api_key)],
    status_code=201,
    tags=["igot"],
)
async def create_enrollment(payload: EnrollmentRequest) -> dict[str, Any]:
    """Self-enrolment. iGOT courses are joined directly by the officer."""
    if not any(c["course_id"] == payload.course_id for c in IGOT_COURSES):
        raise HTTPException(status_code=404, detail=f"No course {payload.course_id}.")

    enrollment_id = f"ENR-{uuid.uuid4().hex[:12].upper()}"
    record = {
        "enrollment_id": enrollment_id,
        "user_ref": payload.user_ref,
        "course_id": payload.course_id,
        "status": "ENROLLED",
        "enrolled_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    ENROLLMENTS[enrollment_id] = record
    return envelope(record)


@app.get("/igot/v1/enrollments", dependencies=[Depends(require_api_key)], tags=["igot"])
async def list_enrollments(user_ref: str | None = None) -> dict[str, Any]:
    rows = [
        r for r in ENROLLMENTS.values() if user_ref is None or r["user_ref"] == user_ref
    ]
    return envelope(rows, count=len(rows))


# ── NSSTA catalogue: dated programmes, nominated for ────────────────────────


@app.get(
    "/nssta/v1/programmes", dependencies=[Depends(require_api_key)], tags=["nssta"]
)
async def list_nssta_programmes(
    competency: str | None = None,
    level: int | None = Query(default=None, ge=1, le=5),
    quarter: Literal["Q1", "Q2", "Q3", "Q4"] | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    rows = _filter(NSSTA_PROGRAMMES, competency, level)
    if quarter:
        months = {"Q1": (1, 3), "Q2": (4, 6), "Q3": (7, 9), "Q4": (10, 12)}[quarter]
        rows = [
            r
            for r in rows
            if r.get("session_start")
            and months[0] <= int(str(r["session_start"]).split("-")[1]) <= months[1]
        ]
    page = rows[offset : offset + limit]
    return envelope(page, count=len(rows))


@app.get(
    "/nssta/v1/programmes/{programme_id}",
    dependencies=[Depends(require_api_key)],
    tags=["nssta"],
)
async def get_nssta_programme(programme_id: str) -> dict[str, Any]:
    for row in NSSTA_PROGRAMMES:
        if row["course_id"] == programme_id:
            return envelope(row)
    raise HTTPException(status_code=404, detail=f"No programme {programme_id}.")


@app.post(
    "/nssta/v1/nominations",
    dependencies=[Depends(require_api_key)],
    status_code=201,
    tags=["nssta"],
)
async def create_nomination(payload: NominationRequest) -> dict[str, Any]:
    """A nomination request, not an enrolment.

    NSSTA programmes are nominated for: the officer requests, a controlling
    authority nominates, and the academy confirms against available seats.
    This endpoint models only the first step, and returns REQUESTED to say so.
    """
    programme = next(
        (p for p in NSSTA_PROGRAMMES if p["course_id"] == payload.programme_id), None
    )
    if programme is None:
        raise HTTPException(
            status_code=404, detail=f"No programme {payload.programme_id}."
        )

    nomination_id = f"NOM-{uuid.uuid4().hex[:12].upper()}"
    record = {
        "nomination_id": nomination_id,
        "user_ref": payload.user_ref,
        "programme_id": payload.programme_id,
        "status": "REQUESTED",
        "nominating_authority": programme.get("nominating_authority"),
        "session_start": programme.get("session_start"),
        "seats": programme.get("seats"),
        "justification": payload.justification,
        "requested_at": datetime.now(tz=timezone.utc).isoformat(),
        "note": (
            "Nomination requested. Approval rests with the controlling authority "
            "and confirmation with the academy; neither step is implemented here."
        ),
    }
    NOMINATIONS[nomination_id] = record
    return envelope(record)


@app.get(
    "/nssta/v1/nominations", dependencies=[Depends(require_api_key)], tags=["nssta"]
)
async def list_nominations(user_ref: str | None = None) -> dict[str, Any]:
    rows = [
        r for r in NOMINATIONS.values() if user_ref is None or r["user_ref"] == user_ref
    ]
    return envelope(rows, count=len(rows))


# ── Meta ─────────────────────────────────────────────────────────────────────


@app.get("/meta/health", tags=["meta"])
async def health() -> dict[str, Any]:
    """Unauthenticated so the platform can probe reachability cheaply."""
    return {
        "status": "ok",
        "is_mock": True,
        "notice": "Mock service. Not an official iGOT or NSSTA API.",
        "igot_courses": len(IGOT_COURSES),
        "nssta_programmes": len(NSSTA_PROGRAMMES),
        "total_records": len(IGOT_COURSES) + len(NSSTA_PROGRAMMES),
        "flaky": FLAKY,
    }


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"service": "mock-catalogue", "docs": "/docs", "health": "/meta/health"}
