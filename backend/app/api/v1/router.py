"""Aggregates every versioned router under /api/v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    assessments,
    assistant,
    auth,
    catalogue,
    competencies,
    gaps,
    materials,
    profiles,
    questions,
    recommendations,
)

api_router = APIRouter()

# M1 · identity
api_router.include_router(auth.router)
api_router.include_router(profiles.router)
# M2 · competency framework
api_router.include_router(competencies.router)
# M4 · skill gap
api_router.include_router(gaps.router)
# M5 · recommendations
api_router.include_router(recommendations.router)
# M6 · catalogue
api_router.include_router(catalogue.router)
# M8 · materials and generated questions
api_router.include_router(materials.router)
api_router.include_router(questions.router)
# M3 · assessments and the closed loop
api_router.include_router(assessments.router)
# M9 · analytics
api_router.include_router(analytics.router)
# M7 · assistant (stub)
api_router.include_router(assistant.router)
