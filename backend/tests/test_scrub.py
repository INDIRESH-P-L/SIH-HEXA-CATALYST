"""The PII boundary.

This is the test to show if a judge asks what leaves the building. It takes a
complete officer record — name, email, employee code, station, phone, Aadhaar —
runs it through the code that builds model context, and asserts none of it
survives into the outbound payload.
"""

from __future__ import annotations

import json

import pytest

from app.ai import scrub
from app.core.errors import PIILeakError

#: A deliberately over-complete profile: everything the database holds about a
#: real officer, including fields the application never sends anywhere.
FULL_PROFILE = {
    "id": "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
    "full_name": "Priya Sharma",
    "email": "priya.sharma@mospi.gov.in",
    "employee_code": "MOSPI/2021/0847",
    "designation": "Statistical Officer",
    "station": "New Delhi",
    "phone": "9876543210",
    "aadhaar": "1234 5678 9012",
    "years_experience": 4,
    "job_role_title": "Statistical Officer",
    "competency_name": "SQL & Database Querying",
    "current_level": 1,
    "required_level": 4,
}


def build_recommendation_context() -> dict[str, object]:
    """Exactly what the recommender assembles, from the full profile above."""
    return scrub.build_context(
        job_role_title=FULL_PROFILE["job_role_title"],
        competency_name=FULL_PROFILE["competency_name"],
        competency_code="SQL",
        current_level=FULL_PROFILE["current_level"],
        required_level=FULL_PROFILE["required_level"],
        gap=3,
        gap_band="HIGH",
        frac_current="below Awareness",
        frac_required="Leveraging for decision-making",
        years_experience_band=scrub.experience_band(FULL_PROFILE["years_experience"]),
        course_title="SQL Fundamentals for Statistical Analysis",
        course_level=2,
        course_duration_hours=12,
        course_format="SELF_PACED",
        provider="iGOT Karmayogi — Capacity Building Commission",
    )


# ── the headline assertion ───────────────────────────────────────────────────


def test_no_personal_data_survives_into_the_model_context() -> None:
    payload = json.dumps(build_recommendation_context())

    assert "Priya" not in payload
    assert "Sharma" not in payload
    assert "priya.sharma@mospi.gov.in" not in payload
    assert "mospi.gov.in" not in payload
    assert "MOSPI/2021/0847" not in payload
    assert "9876543210" not in payload
    assert "1234 5678 9012" not in payload
    assert "New Delhi" not in payload
    assert FULL_PROFILE["id"] not in payload


def test_exact_years_of_experience_is_coarsened_to_a_band() -> None:
    """Four years plus a role plus a station can identify one officer. A band cannot."""
    context = build_recommendation_context()
    assert context["years_experience_band"] == "3-5"
    assert "4" not in str(context["years_experience_band"])


def test_the_context_still_carries_what_the_model_needs() -> None:
    """Scrubbing must not gut the prompt."""
    context = build_recommendation_context()
    assert context["competency_name"] == "SQL & Database Querying"
    assert context["current_level"] == 1
    assert context["required_level"] == 4
    assert context["gap_band"] == "HIGH"
    assert context["course_title"].startswith("SQL Fundamentals")


# ── the whitelist ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "field",
    ["full_name", "email", "employee_code", "station", "phone", "aadhaar", "user_id"],
)
def test_identifying_fields_are_rejected_not_silently_dropped(field: str) -> None:
    """Dropping an unexpected key quietly is how a leak ships unnoticed."""
    with pytest.raises(PIILeakError):
        scrub.build_context(**{field: "anything"})


def test_an_unknown_field_is_rejected_even_if_it_looks_harmless() -> None:
    with pytest.raises(PIILeakError):
        scrub.build_context(competency_name="SQL", favourite_colour="blue")


def test_none_values_are_dropped_so_callers_need_no_branching() -> None:
    context = scrub.build_context(competency_name="SQL", course_title=None)
    assert context == {"competency_name": "SQL"}


def test_work_related_name_fields_are_allowed() -> None:
    """competency_name and course_title describe work, not people."""
    context = scrub.build_context(
        competency_name="SQL", course_title="SQL Basics", job_role_title="Statistical Officer"
    )
    assert len(context) == 3


# ── assert_no_pii, the second line of defence ────────────────────────────────


def test_assert_no_pii_passes_a_clean_prompt() -> None:
    scrub.assert_no_pii(json.dumps(build_recommendation_context()))


@pytest.mark.parametrize(
    ("payload", "kind"),
    [
        ("Contact priya.sharma@mospi.gov.in about this", "email address"),
        ("Her number is 9876543210", "phone number"),
        ("Aadhaar 1234 5678 9012 on file", "Aadhaar-like number"),
        ("Officer 3f2504e0-4f89-11d3-9a0c-0305e82c3301 scored 85", "uuid"),
        ("Employee MOSPI/2021/0847 needs training", "employee code"),
    ],
)
def test_assert_no_pii_blocks_a_hand_assembled_prompt(payload: str, kind: str) -> None:
    """Catches anything built by hand that bypassed build_context."""
    with pytest.raises(PIILeakError) as excinfo:
        scrub.assert_no_pii(payload)
    assert kind in str(excinfo.value)


def test_find_pii_reports_every_kind_present() -> None:
    found = scrub.find_pii("priya@x.gov.in / 9876543210 / MOSPI/2021/0847")
    assert set(found) == {"email address", "phone number", "employee code"}


# ── experience banding ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("years", "band"),
    [(0, "0-2"), (2, "0-2"), (3, "3-5"), (5, "3-5"), (6, "6-10"), (10, "6-10"),
     (11, "11-20"), (20, "11-20"), (21, "20+"), (None, "unspecified")],
)
def test_experience_bands(years: int | None, band: str) -> None:
    assert scrub.experience_band(years) == band
