"""M4 · gap engine.

Pure functions, no database, no HTTP. If the arithmetic behind the central
claim of the product is wrong, it fails here in milliseconds.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.services import m4_gap_engine as engine


def req(
    code: str,
    required: int,
    criticality: float = 1.0,
    horizon: str = "current_role",
    decay: str = "methodology",
    is_new: bool = False,
) -> engine.Requirement:
    return engine.Requirement(
        competency_id=f"id-{code}",
        competency_code=code,
        competency_name=f"{code} competency",
        cluster="TECHNICAL",
        required_level=required,
        criticality=criticality,
        horizon=horizon,
        decay=decay,
        is_new_in_version=is_new,
    )


def obs(level: int, confidence: float = 0.9, **kwargs) -> engine.Observation:
    return engine.Observation(
        level=level,
        confidence=confidence,
        source_type=kwargs.get("source_type", "assessment"),
        assessed_at=kwargs.get("assessed_at"),
    )


# ── the FRAC scale ───────────────────────────────────────────────────────────


def test_frac_is_a_four_point_scale() -> None:
    """The only scale used anywhere in the platform."""
    assert engine.MAX_LEVEL == 4
    assert engine.FRAC_LABELS[1] == "Awareness"
    assert engine.FRAC_LABELS[2] == "Application"
    assert engine.FRAC_LABELS[3] == "Leveraging for decisions"
    assert engine.FRAC_LABELS[4] == "Subject Matter Expert"


def test_level_zero_is_not_part_of_frac() -> None:
    """No evidence on file is a different statement from the lowest rung."""
    assert engine.FRAC_LABELS[0] == "No evidence"
    assert engine.NO_EVIDENCE_LEVEL == 0


def test_frac_label_clamps_out_of_range() -> None:
    assert engine.frac_label(9) == engine.frac_label(4)
    assert engine.frac_label(-2) == engine.frac_label(0)


# ── compute_gap ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("required", "current", "expected"),
    [(4, 1, 3), (4, 4, 0), (3, 3, 0), (2, 4, 0), (4, 0, 4), (1, 0, 1)],
)
def test_compute_gap(required: int, current: int, expected: int) -> None:
    assert engine.compute_gap(required, current) == expected


def test_gap_is_never_negative() -> None:
    """Exceeding a requirement is a strength, not a negative gap.

    Negatives would let a strong competency mathematically offset a weak one in
    any aggregate, which is exactly wrong for capacity planning.
    """
    assert engine.compute_gap(2, 4) == 0


# ── bands ────────────────────────────────────────────────────────────────────


def test_two_levels_below_on_a_critical_competency_is_critical() -> None:
    assert (
        engine.band_for(2, criticality=2.5, current_level=1, required_level=3)
        is engine.GapBand.CRITICAL
    )


def test_two_levels_below_on_an_incidental_competency_is_only_significant() -> None:
    """Otherwise CRITICAL stops meaning anything and every dashboard is red."""
    assert (
        engine.band_for(2, criticality=1.2, current_level=1, required_level=3)
        is engine.GapBand.SIGNIFICANT
    )


def test_one_level_below_is_significant() -> None:
    assert (
        engine.band_for(1, criticality=3.0, current_level=3, required_level=4)
        is engine.GapBand.SIGNIFICANT
    )


def test_at_expectation_is_met() -> None:
    assert engine.band_for(0, current_level=3, required_level=3) is engine.GapBand.MET


def test_above_expectation_is_a_strength() -> None:
    """A candidate mentor, not a zero."""
    assert engine.band_for(0, current_level=4, required_level=2) is engine.GapBand.STRENGTH


def test_a_next_role_requirement_is_emerging() -> None:
    assert (
        engine.band_for(3, criticality=3.0, horizon="next_role", current_level=1, required_level=4)
        is engine.GapBand.EMERGING
    )


def test_a_requirement_new_in_this_framework_version_is_emerging() -> None:
    """An emerging gap needs no forecasting model — diff the sealed versions."""
    assert (
        engine.band_for(2, criticality=3.0, current_level=1, required_level=3, is_new_in_version=True)
        is engine.GapBand.EMERGING
    )


# ── priority ─────────────────────────────────────────────────────────────────


def test_priority_formula() -> None:
    """priority = gap x criticality x (2 - confidence) x horizon"""
    assert engine.priority_for(3, 2.2, 0.25, "current_role") == pytest.approx(11.55)
    assert engine.priority_for(1, 2.2, 0.90, "current_role") == pytest.approx(2.42)


def test_a_met_competency_has_zero_priority() -> None:
    assert engine.priority_for(0, 3.0, 0.25, "current_role") == 0.0


def test_low_confidence_nearly_doubles_priority() -> None:
    """The term that matters.

    An unmeasured competency sits near 0.25 confidence, which the engine
    surfaces as urgent — "we do not know whether this officer can do this" is
    the honest position and the one that drives people into assessment.
    """
    unmeasured = engine.priority_for(2, 2.0, 0.25, "current_role")
    measured = engine.priority_for(2, 2.0, 1.00, "current_role")
    assert unmeasured == pytest.approx(measured * 1.75)


def test_next_role_horizon_discounts_rather_than_ignores() -> None:
    current = engine.priority_for(2, 2.0, 0.9, "current_role")
    future = engine.priority_for(2, 2.0, 0.9, "next_role")
    assert future == pytest.approx(current * 0.6)
    assert future > 0, "a next-role requirement is real, just not yet urgent"


def test_criticality_reorders_equal_gaps() -> None:
    assert engine.priority_for(1, 3.0, 0.9, "current_role") > engine.priority_for(
        1, 1.0, 0.9, "current_role"
    )


# ── decay ────────────────────────────────────────────────────────────────────


def test_behavioural_competencies_do_not_decay() -> None:
    long_ago = datetime.now(tz=timezone.utc) - timedelta(days=4000)
    assert engine.is_stale("behavioural", long_ago) is False


@pytest.mark.parametrize(
    ("decay", "months", "expected"),
    [
        ("tools_platforms", 19, True),
        ("tools_platforms", 12, False),
        ("regulatory_procedural", 13, True),
        ("regulatory_procedural", 6, False),
        ("methodology", 37, True),
        ("methodology", 24, False),
    ],
)
def test_decay_classes(decay: str, months: int, expected: bool) -> None:
    assessed = datetime.now(tz=timezone.utc) - timedelta(days=int(months * 30.44))
    assert engine.is_stale(decay, assessed) is expected


def test_stale_evidence_raises_priority_without_rewriting_the_level() -> None:
    """Decay lowers confidence. It never silently demotes an officer."""
    long_ago = datetime.now(tz=timezone.utc) - timedelta(days=1200)
    row = engine.build_gap_row(
        req("SQL", 4, 2.0, decay="tools_platforms"),
        obs(2, confidence=0.9, assessed_at=long_ago),
    )
    assert row.current_level == 2, "the level is unchanged"
    assert row.stale is True
    assert row.confidence <= engine.STALE_CONFIDENCE
    assert row.needs_reassessment is True


def test_fresh_evidence_keeps_its_confidence() -> None:
    recent = datetime.now(tz=timezone.utc) - timedelta(days=30)
    row = engine.build_gap_row(
        req("SQL", 4, 2.0, decay="tools_platforms"),
        obs(2, confidence=0.9, assessed_at=recent),
    )
    assert row.stale is False
    assert row.confidence == pytest.approx(0.9)


# ── derivation ───────────────────────────────────────────────────────────────


def test_every_gap_carries_its_derivation() -> None:
    """The interface shows the arithmetic, so it has to be persisted."""
    row = engine.build_gap_row(req("SQL", 4, 2.2), obs(1, confidence=0.25))
    assert row.derivation is not None
    for term in (
        "expected",
        "current",
        "difference",
        "criticality",
        "confidence",
        "uncertainty_multiplier",
        "horizon_multiplier",
        "priority",
        "formula",
    ):
        assert term in row.derivation


def test_derivation_multiplies_out_to_the_stated_priority() -> None:
    row = engine.build_gap_row(req("SQL", 4, 2.2), obs(1, confidence=0.25))
    d = row.derivation
    assert d is not None
    product = (
        d["difference"] * d["criticality"] * d["uncertainty_multiplier"] * d["horizon_multiplier"]
    )
    assert product == pytest.approx(row.priority)


# ── the demonstration profile ────────────────────────────────────────────────


def test_priya_sql_before_assessment() -> None:
    """Required 4, self-declared 1: a CRITICAL gap at priority 11.55."""
    row = engine.build_gap_row(req("SQL", 4, 2.2), engine.Observation(level=1, confidence=0.25))
    assert row.gap == 3
    assert row.band is engine.GapBand.CRITICAL
    assert row.priority == pytest.approx(11.55)
    assert row.frac_current == "Awareness"
    assert row.frac_required == "Subject Matter Expert"


def test_priya_sql_after_a_proctored_assessment() -> None:
    """Level 3 at 0.90 confidence: SIGNIFICANT, and priority collapses."""
    row = engine.build_gap_row(req("SQL", 4, 2.2), obs(3, confidence=0.90))
    assert row.gap == 1
    assert row.band is engine.GapBand.SIGNIFICANT
    assert row.priority == pytest.approx(2.42)


def test_the_demonstration_profile_produces_a_readable_spread() -> None:
    requirements = [
        req("SQL", 4, 2.2),
        req("SAMPLING", 4, 2.5),
        req("SURVEY_DESIGN", 3, 2.0),
        req("PYTHON", 3, 1.8),
        req("DATA_VIZ", 3, 1.5),
        req("PROJECT_MGMT", 3, 1.4),
        req("GIS", 2, 1.2),
        req("DATA_QUALITY", 3, 2.0, horizon="next_role"),
    ]
    observations = {
        "id-SQL": engine.Observation(1, 0.25, "self_declared"),
        "id-SAMPLING": engine.Observation(3, 0.25, "self_declared"),
        "id-SURVEY_DESIGN": engine.Observation(3, 0.25, "self_declared"),
        "id-PYTHON": engine.Observation(2, 0.25, "self_declared"),
        "id-DATA_VIZ": engine.Observation(2, 0.25, "self_declared"),
        "id-PROJECT_MGMT": engine.Observation(2, 0.25, "self_declared"),
        "id-GIS": engine.Observation(1, 0.25, "self_declared"),
        # DATA_QUALITY has no evidence at all.
    }
    rows = engine.build_gap_rows(requirements, observations)
    summary = engine.summarise(rows)

    assert (summary.critical, summary.significant, summary.emerging, summary.met) == (1, 5, 1, 1)
    assert rows[0].competency_code == "SQL"
    assert summary.unassessed_count == 1


# ── missing evidence ─────────────────────────────────────────────────────────


def test_a_competency_with_no_evidence_is_a_finding_not_a_blank() -> None:
    rows = engine.build_gap_rows([req("CLOUD", 3, 2.0)], {})
    assert len(rows) == 1
    assert rows[0].current_level == 0
    assert rows[0].gap == 3
    assert rows[0].source_type is None
    assert rows[0].needs_reassessment is True


# ── ordering ─────────────────────────────────────────────────────────────────


def test_rows_sort_by_priority_descending() -> None:
    rows = engine.build_gap_rows(
        [req("A", 4, 1.0), req("B", 4, 3.0), req("C", 2, 1.0)],
        {k: engine.Observation(1, 0.9, "assessment") for k in ("id-A", "id-B", "id-C")},
    )
    assert [r.competency_code for r in rows] == ["B", "A", "C"]


def test_ordering_is_stable_for_equal_priority() -> None:
    """A list that reshuffles on refresh looks broken."""
    observations = {"id-ZULU": engine.Observation(2, 0.9), "id-ALPHA": engine.Observation(2, 0.9)}
    first = engine.build_gap_rows([req("ZULU", 3), req("ALPHA", 3)], observations)
    second = engine.build_gap_rows([req("ALPHA", 3), req("ZULU", 3)], observations)
    assert [r.competency_code for r in first] == [r.competency_code for r in second]


# ── selection ────────────────────────────────────────────────────────────────


def test_target_gaps_excludes_met_and_caps_the_list() -> None:
    requirements = [req(c, 4, 2.0) for c in "ABCDEF"] + [req("MET", 1, 1.0)]
    observations = {f"id-{c}": engine.Observation(1, 0.9) for c in "ABCDEF"}
    observations["id-MET"] = engine.Observation(3, 0.9)

    targets = engine.target_gaps(engine.build_gap_rows(requirements, observations), limit=5)
    assert len(targets) == 5
    assert all(t.gap >= 1 for t in targets)
    assert "MET" not in {t.competency_code for t in targets}


def test_reassessment_candidates_are_stale_or_unmeasured() -> None:
    long_ago = datetime.now(tz=timezone.utc) - timedelta(days=1200)
    rows = engine.build_gap_rows(
        [req("FRESH", 3, decay="tools_platforms"), req("OLD", 3, decay="tools_platforms"), req("NONE", 3)],
        {
            "id-FRESH": obs(2, 0.9, assessed_at=datetime.now(tz=timezone.utc)),
            "id-OLD": obs(2, 0.9, assessed_at=long_ago),
        },
    )
    codes = {r.competency_code for r in engine.reassessment_candidates(rows)}
    assert codes == {"OLD", "NONE"}


# ── prerequisites ────────────────────────────────────────────────────────────


def test_empty_prerequisites_are_satisfied() -> None:
    assert engine.prerequisites_satisfied([], {}) is True


def test_prerequisite_needs_evidence() -> None:
    assert engine.prerequisites_satisfied(["SQL"], {"SQL": 1}) is True
    assert engine.prerequisites_satisfied(["SQL"], {"SQL": 0}) is False
    assert engine.prerequisites_satisfied(["SQL"], {}) is False


def test_all_prerequisites_must_be_met() -> None:
    levels = {"SQL": 2, "PYTHON": 0}
    assert engine.prerequisites_satisfied(["SQL", "PYTHON"], levels) is False
    assert engine.prerequisites_satisfied(["SQL"], levels) is True


# ── summary ──────────────────────────────────────────────────────────────────


def test_summary_of_an_empty_requirement_set_does_not_divide_by_zero() -> None:
    summary = engine.summarise([])
    assert summary.total_competencies == 0
    assert summary.average_current_level == 0.0
    assert summary.top_gaps == []
