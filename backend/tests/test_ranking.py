"""M5 · retrieval fusion, ranking and sequencing.

The three stages exist because collapsing them into one similarity search
produces recommendations that are topically plausible and operationally
useless. These tests are mostly about that distinction.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.services import m5_ranking as ranking


def offering(
    course_id: str,
    *,
    level: int = 2,
    hours: int = 12,
    fmt: str = "SELF_PACED",
    competency: str = "SQL",
    prerequisites: list[str] | None = None,
    session_start: date | None = None,
    synced_days_ago: int = 0,
    language: str = "en",
    department_priority: float = 0.0,
) -> ranking.Offering:
    return ranking.Offering(
        course_id=course_id,
        external_id=course_id,
        source="IGOT",
        title=f"Course {course_id}",
        competency_code=competency,
        proficiency_level=level,
        duration_hours=hours,
        learning_format=fmt,
        prerequisites=prerequisites or [],
        session_start=session_start,
        synced_days_ago=synced_days_ago,
        language=language,
        department_priority=department_priority,
    )


# ── Stage 1 · fusion ─────────────────────────────────────────────────────────


def test_the_weights_sum_to_one() -> None:
    assert sum(ranking.WEIGHTS.values()) == pytest.approx(1.0)


def test_there_are_seven_ranking_terms() -> None:
    assert set(ranking.WEIGHTS) == {
        "gap_priority",
        "semantic_similarity",
        "level_fit",
        "prerequisites_met",
        "effort_fit",
        "department_priority",
        "recency_language",
    }


def test_fusion_needs_only_ordering_not_comparable_scores() -> None:
    """A dense retriever returns cosine similarity and BM25 returns a
    term-frequency score. Normalising those onto one axis requires assumptions
    that do not hold; reciprocal rank fusion needs only the ordering."""
    dense = [ranking.RankedHit("a", 1, 0.91), ranking.RankedHit("b", 2, 0.88)]
    lexical = [ranking.RankedHit("b", 1, 42.0), ranking.RankedHit("c", 2, 17.0)]

    fused = ranking.reciprocal_rank_fusion([dense, lexical])
    # b places 2nd and 1st; a places 1st once. b should win on the pair.
    assert fused["b"] > fused["a"] > fused["c"]


def test_an_item_found_by_every_retriever_outranks_one_found_by_only_one() -> None:
    ranked = [ranking.RankedHit("agreed", 1)], [ranking.RankedHit("agreed", 1)]
    solo = [ranking.RankedHit("solo", 1)]
    fused = ranking.reciprocal_rank_fusion([ranked[0], ranked[1], solo])
    assert fused["agreed"] > fused["solo"]


def test_fusion_normalises_onto_zero_to_one() -> None:
    fused = ranking.normalise_fusion({"a": 0.02, "b": 0.01})
    assert fused["a"] == 1.0
    assert 0.0 < fused["b"] < 1.0


def test_normalising_an_empty_fusion_is_safe() -> None:
    assert ranking.normalise_fusion({}) == {}


# ── Stage 2 · level fit ──────────────────────────────────────────────────────


def test_level_fit_peaks_one_rung_above_the_officer() -> None:
    """Recommend the next rung, not the top of the ladder."""
    assert ranking.level_fit(course_level=2, current_level=1) == 1.0


def test_level_fit_falls_away_over_the_four_point_scale() -> None:
    assert ranking.level_fit(3, 1) == pytest.approx(2 / 3)
    assert ranking.level_fit(4, 1) == pytest.approx(1 / 3)
    assert ranking.level_fit(1, 1) == pytest.approx(2 / 3)


def test_an_sme_module_scores_poorly_for_an_officer_at_awareness() -> None:
    assert ranking.level_fit(4, 1) < ranking.level_fit(2, 1)


def test_level_fit_never_goes_negative() -> None:
    assert ranking.level_fit(4, 0) >= 0.0


# ── Stage 2 · effort fit ─────────────────────────────────────────────────────


def test_anything_inside_one_month_of_study_scores_full_marks() -> None:
    assert ranking.effort_fit(duration_hours=8, monthly_hours=8) == 1.0
    assert ranking.effort_fit(duration_hours=4, monthly_hours=8) == 1.0


def test_effort_fit_decays_with_the_months_required() -> None:
    """A three-week residential programme proposed to an officer with four
    hours a month is the failure this term exists to prevent."""
    assert ranking.effort_fit(40, monthly_hours=8) == pytest.approx(0.2)
    assert ranking.effort_fit(16, monthly_hours=8) == pytest.approx(0.5)


def test_a_long_programme_is_outranked_not_excluded() -> None:
    assert ranking.effort_fit(40, monthly_hours=8) > 0.0


def test_self_paced_is_easier_to_fit_around_duty() -> None:
    assert ranking.format_effort_note("SELF_PACED") == 1.0
    assert ranking.format_effort_note("CLASSROOM") == 0.7


# ── Stage 2 · recency and language ───────────────────────────────────────────


def test_a_freshly_synced_record_in_the_officers_language_scores_highest() -> None:
    assert ranking.recency_language_fit(0, "en", "en") == 1.0


def test_a_stale_record_scores_lower() -> None:
    assert ranking.recency_language_fit(300, "en", "en") < ranking.recency_language_fit(
        10, "en", "en"
    )


def test_a_language_mismatch_costs_but_does_not_exclude() -> None:
    matched = ranking.recency_language_fit(0, "en", "en")
    mismatched = ranking.recency_language_fit(0, "hi", "en")
    assert 0.0 < mismatched < matched


# ── Stage 2 · the weighted score ─────────────────────────────────────────────


def test_every_term_is_returned_for_display() -> None:
    _score, terms = ranking.score_offering(
        offering("a"), gap_priority_normalised=1.0, similarity=0.9, current_level=1,
        prerequisites_met=True,
    )
    assert set(terms) == set(ranking.WEIGHTS)


def test_a_perfect_candidate_approaches_one() -> None:
    score, _terms = ranking.score_offering(
        offering("a", level=2, hours=8),
        gap_priority_normalised=1.0,
        similarity=1.0,
        current_level=1,
        prerequisites_met=True,
    )
    # department_priority is 0 by default, so the ceiling is 1 - 0.08.
    assert score == pytest.approx(0.92, abs=0.01)


def test_an_unmet_prerequisite_costs_exactly_its_weight() -> None:
    met, _ = ranking.score_offering(
        offering("a"), gap_priority_normalised=1.0, similarity=0.8, current_level=1,
        prerequisites_met=True,
    )
    unmet, _ = ranking.score_offering(
        offering("a"), gap_priority_normalised=1.0, similarity=0.8, current_level=1,
        prerequisites_met=False,
    )
    assert met - unmet == pytest.approx(ranking.WEIGHTS["prerequisites_met"])


def test_departmental_priority_can_lift_a_course() -> None:
    plain, _ = ranking.score_offering(
        offering("a"), gap_priority_normalised=0.5, similarity=0.5, current_level=1,
        prerequisites_met=True,
    )
    pushed, _ = ranking.score_offering(
        offering("a", department_priority=1.0),
        gap_priority_normalised=0.5, similarity=0.5, current_level=1, prerequisites_met=True,
    )
    assert pushed - plain == pytest.approx(ranking.WEIGHTS["department_priority"])


# ── Stage 2 · constraints and diversity ──────────────────────────────────────


def test_completed_courses_are_removed_outright() -> None:
    _pinned, rankable = ranking.apply_hard_constraints(
        [offering("done"), offering("new")], completed_ids={"done"}
    )
    assert [o.course_id for o in rankable] == ["new"]


def test_mandatory_courses_are_pinned_rather_than_ranked() -> None:
    """A compliance requirement is not a recommendation."""
    pinned, rankable = ranking.apply_hard_constraints(
        [offering("must"), offering("maybe")], completed_ids=set(), mandatory_ids={"must"}
    )
    assert [o.course_id for o in pinned] == ["must"]
    assert [o.course_id for o in rankable] == ["maybe"]


def test_one_large_gap_cannot_fill_the_whole_list() -> None:
    scored = [(0.9 - i / 100, offering(f"sql{i}", competency="SQL"), "SQL") for i in range(4)]
    scored.append((0.5, offering("py", competency="PYTHON"), "PYTHON"))

    kept = ranking.cap_per_competency(scored, max_per_competency=2)
    codes = [code for _s, _o, code in kept]
    assert codes.count("SQL") == 2
    assert codes.count("PYTHON") == 1


def test_the_cap_keeps_the_highest_scored_of_each_competency() -> None:
    scored = [(0.9 - i / 100, offering(f"sql{i}"), "SQL") for i in range(5)]
    kept = ranking.cap_per_competency(scored, max_per_competency=2)
    assert [o.course_id for _s, o, _c in kept] == ["sql0", "sql1"]


# ── Stage 3 · sequencing ─────────────────────────────────────────────────────


def test_a_prerequisite_is_ordered_before_what_depends_on_it() -> None:
    basics = offering("basics", competency="SQL", level=1)
    advanced = offering("advanced", competency="PYTHON", level=3, prerequisites=["SQL"])

    ordered = ranking.topological_order([advanced, basics], levels_by_code={})
    assert [o.course_id for o in ordered] == ["basics", "advanced"]


def test_a_prerequisite_the_officer_already_holds_creates_no_constraint() -> None:
    basics = offering("basics", competency="SQL", level=1)
    advanced = offering("advanced", competency="PYTHON", level=3, prerequisites=["SQL"])

    ordered = ranking.topological_order([advanced, basics], levels_by_code={"SQL": 3})
    # No edge, so ordering falls back to level then title: both are free.
    assert {o.course_id for o in ordered} == {"basics", "advanced"}


def test_sequencing_is_stable_not_merely_valid() -> None:
    items = [offering("b", level=2), offering("a", level=1)]
    first = ranking.topological_order(items, {})
    second = ranking.topological_order(list(reversed(items)), {})
    assert [o.course_id for o in first] == [o.course_id for o in second]


def test_a_prerequisite_cycle_degrades_rather_than_raising() -> None:
    """A malformed catalogue must not take the whole recommendation down."""
    a = offering("a", competency="A", prerequisites=["B"])
    b = offering("b", competency="B", prerequisites=["A"])
    ordered = ranking.topological_order([a, b], {})
    assert len(ordered) == 2


def test_empty_input_sequences_to_nothing() -> None:
    assert ranking.topological_order([], {}) == []


# ── Stage 3 · calendar placement ─────────────────────────────────────────────


def test_a_pathway_is_laid_out_against_an_hour_budget() -> None:
    steps = ranking.place_on_calendar(
        [offering("a", hours=8), offering("b", hours=8)],
        start=date(2026, 1, 1),
        monthly_hours=8,
    )
    assert [s.order for s in steps] == [1, 2]
    assert steps[1].starts_on >= steps[0].ends_on


def test_a_dated_programme_anchors_to_its_own_session() -> None:
    """The academy decides when a residential programme happens; self-paced
    study flows around it."""
    session = date(2026, 6, 1)
    steps = ranking.place_on_calendar(
        [offering("selfpaced", hours=8), offering("dated", hours=40, session_start=session)],
        start=date(2026, 1, 1),
        monthly_hours=8,
    )
    dated = next(s for s in steps if s.offering.course_id == "dated")
    assert dated.anchored is True
    assert dated.starts_on == session


def test_an_anchored_programme_does_not_block_self_paced_study() -> None:
    steps = ranking.place_on_calendar(
        [
            offering("dated", hours=40, session_start=date(2026, 9, 1)),
            offering("selfpaced", hours=8),
        ],
        start=date(2026, 1, 1),
        monthly_hours=8,
    )
    selfpaced = next(s for s in steps if s.offering.course_id == "selfpaced")
    assert selfpaced.starts_on == date(2026, 1, 1)


def test_longer_courses_occupy_more_of_the_budget() -> None:
    steps = ranking.place_on_calendar(
        [offering("long", hours=40)], start=date(2026, 1, 1), monthly_hours=8
    )
    assert steps[0].months_required == pytest.approx(5.0)


def test_total_hours_is_reported_for_the_pathway() -> None:
    steps = ranking.place_on_calendar(
        [offering("a", hours=12), offering("b", hours=20)],
        start=date(2026, 1, 1),
    )
    assert ranking.pathway_total_hours(steps) == 32
