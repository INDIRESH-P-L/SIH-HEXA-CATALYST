"""M3 · difficulty-weighted scoring and the competency update rule.

The scorer is a pure function of (responses, item metadata, cut-scores).
Re-running it on stored responses must reproduce the number exactly — that is
the audit test, and these are the cases it has to survive.
"""

from __future__ import annotations

import pytest

from app.services import m3_scoring as scoring


def answer(correct: bool, difficulty: str = "medium", topic: str | None = None, attempted: bool = True):
    return scoring.AnsweredQuestion(
        question_id=f"q-{difficulty}-{correct}-{topic}",
        correct_index=1,
        selected_index=(1 if correct else 2) if attempted else None,
        difficulty=difficulty,
        topic=topic,
    )


def paper(easy: tuple[int, int], medium: tuple[int, int], hard: tuple[int, int]):
    """Build a paper as (correct, total) per difficulty band."""
    items = []
    for difficulty, (correct, total) in (("easy", easy), ("medium", medium), ("hard", hard)):
        items += [answer(True, difficulty) for _ in range(correct)]
        items += [answer(False, difficulty) for _ in range(total - correct)]
    return items


# ── the worked example from the architecture ─────────────────────────────────


def test_the_documented_worked_example() -> None:
    """easy 3/4, medium 2/3, hard 1/3.

        numerator   = (1x3) + (2x2) + (3x1) = 10
        denominator = (1x4) + (2x3) + (3x3) = 19
        score       = 52.6 %

    The same paper reads 60 % unweighted. The weighting correctly penalises
    failure on the items that discriminate.
    """
    result = scoring.score_assessment(paper(easy=(3, 4), medium=(2, 3), hard=(1, 3)))
    assert result.numerator == 10
    assert result.denominator == 19
    assert result.weighted_score == pytest.approx(52.63, abs=0.01)
    assert result.raw_score == pytest.approx(60.0)


def test_weighting_penalises_failure_on_hard_items() -> None:
    """Two papers, same raw score, different weighted score."""
    missed_hard = scoring.score_assessment(paper(easy=(4, 4), medium=(3, 3), hard=(1, 3)))
    missed_easy = scoring.score_assessment(paper(easy=(2, 4), medium=(3, 3), hard=(3, 3)))
    assert missed_hard.raw_score == pytest.approx(missed_easy.raw_score)
    assert missed_hard.weighted_score < missed_easy.weighted_score


def test_weights_are_one_two_three() -> None:
    assert scoring.DIFFICULTY_WEIGHT == {"easy": 1, "medium": 2, "hard": 3}


# ── attempted items only ─────────────────────────────────────────────────────


def test_only_attempted_items_enter_the_denominator() -> None:
    """Abandoning an assessment must not deflate the items that were answered."""
    items = [answer(True, "hard"), answer(False, "easy", attempted=False)]
    result = scoring.score_assessment(items)
    assert result.attempted == 1
    assert result.denominator == 3
    assert result.weighted_score == 100.0
    assert result.total_items == 2, "the attempt count still travels with the result"


def test_an_empty_paper_scores_zero_rather_than_dividing_by_zero() -> None:
    result = scoring.score_assessment([])
    assert result.weighted_score == 0.0
    assert result.denominator == 0


def test_the_breakdown_serialises_for_display() -> None:
    payload = scoring.score_assessment(paper((3, 4), (2, 3), (1, 3))).as_dict()
    assert payload["numerator"] == 10
    assert payload["denominator"] == 19
    assert payload["per_difficulty"]["hard"] == {"correct": 1, "attempted": 3}
    assert "sum(w_i * c_i)" in payload["formula"]


# ── cut-scores ───────────────────────────────────────────────────────────────


def test_cut_scores_map_a_score_onto_the_frac_scale() -> None:
    cuts = scoring.CutScores(level_1_min=40, level_2_min=60, level_3_min=78, level_4_min=90)
    assert cuts.level_for(95) == 4
    assert cuts.level_for(90) == 4
    assert cuts.level_for(89.9) == 3
    assert cuts.level_for(78) == 3
    assert cuts.level_for(60) == 2
    assert cuts.level_for(40) == 1
    assert cuts.level_for(39.9) == 0


def test_cut_scores_are_per_competency_not_one_global_threshold() -> None:
    """60% on sampling theory and 60% on spreadsheet hygiene are not the same
    statement about an officer."""
    lenient = scoring.CutScores(level_1_min=40, level_2_min=58, level_3_min=76, level_4_min=90)
    strict = scoring.CutScores(level_1_min=50, level_2_min=70, level_3_min=85, level_4_min=95)
    assert lenient.level_for(77) == 3
    assert strict.level_for(77) == 2


# ── the update rule ──────────────────────────────────────────────────────────


def test_the_level_measured_is_the_level_recorded() -> None:
    """An assessment measures where an officer is, not how far they moved.

    Demonstrating level 3 records level 3, even from a starting point of 1.
    """
    cuts = scoring.CutScores()
    assert scoring.next_level(current=1, score=82.0, n_attempted=20, cut_scores=cuts) == 3


def test_level_never_decreases() -> None:
    """A poor result flags a revisit; it never demotes the officer on one bad
    afternoon. Decay handles genuine loss of currency, by lowering confidence."""
    cuts = scoring.CutScores()
    for score in (0.0, 25.0, 45.0, 59.0):
        assert scoring.next_level(current=3, score=score, n_attempted=20, cut_scores=cuts) == 3


def test_too_few_items_changes_nothing() -> None:
    """Four items going well is not evidence of a level."""
    cuts = scoring.CutScores()
    assert scoring.next_level(current=1, score=100.0, n_attempted=4, cut_scores=cuts) == 1
    assert scoring.next_level(current=1, score=100.0, n_attempted=5, cut_scores=cuts) == 4


def test_level_is_capped_at_four() -> None:
    assert scoring.next_level(current=4, score=100.0, n_attempted=20) == 4


def test_revisit_is_set_below_the_level_two_boundary() -> None:
    cuts = scoring.CutScores(level_2_min=60)
    assert scoring.needs_revisit(59.9, cuts) is True
    assert scoring.needs_revisit(60.0, cuts) is False


# ── delivery mode ────────────────────────────────────────────────────────────


def test_proctored_and_practice_carry_different_confidence() -> None:
    """Practice attempts are real evidence for the learner and noise for
    workforce planning."""
    assert scoring.confidence_for_mode("proctored") == 0.90
    assert scoring.confidence_for_mode("practice") == 0.50
    assert scoring.confidence_for_mode("anything else") == 0.50


# ── topics ───────────────────────────────────────────────────────────────────


def test_weak_topics_weight_hard_items_more_heavily() -> None:
    items = [
        answer(False, "hard", "JOIN types"),
        answer(False, "easy", "GROUP BY"),
        answer(False, "easy", "GROUP BY"),
        answer(False, "easy", "GROUP BY"),
    ]
    # GROUP BY is missed three times at weight 1; JOIN types once at weight 3.
    assert scoring.weak_topics(items)[0] == "GROUP BY"
    assert set(scoring.weak_topics(items)) == {"GROUP BY", "JOIN types"}


def test_weak_topics_ignores_correct_answers_and_is_capped() -> None:
    items = [answer(False, "medium", f"topic {i}") for i in range(5)]
    items.append(answer(True, "medium", "mastered"))
    topics = scoring.weak_topics(items, limit=3)
    assert len(topics) == 3
    assert "mastered" not in topics


def test_weak_topic_ties_break_alphabetically_for_stable_output() -> None:
    items = [answer(False, "medium", "Zebra"), answer(False, "medium", "Alpha")]
    assert scoring.weak_topics(items) == ["Alpha", "Zebra"]


def test_untagged_items_do_not_produce_empty_topics() -> None:
    items = [answer(False, "medium", None), answer(False, "medium", "   ")]
    assert scoring.weak_topics(items) == []


def test_strong_topics_exclude_anything_also_answered_wrong() -> None:
    items = [
        answer(True, "medium", "JOIN types"),
        answer(False, "medium", "JOIN types"),
        answer(True, "medium", "SELECT"),
    ]
    assert scoring.strong_topics(items) == ["SELECT"]


# ── calibration ──────────────────────────────────────────────────────────────


def test_ability_rises_on_a_correct_answer_and_falls_on_a_wrong_one() -> None:
    assert scoring.update_ability(0.0, 0.0, correct=True) > 0.0
    assert scoring.update_ability(0.0, 0.0, correct=False) < 0.0


def test_an_item_strong_candidates_miss_gets_harder() -> None:
    """Elo difficulty, learned live and shadowing the authored estimate."""
    assert scoring.update_item_difficulty(0.0, ability=2.0, correct=False) > 0.0
    assert scoring.update_item_difficulty(0.0, ability=2.0, correct=True) < 0.0


def test_observed_difficulty_is_withheld_until_there_is_enough_evidence() -> None:
    """Replacing an authored difficulty from four responses is worse than
    leaving it alone."""
    assert scoring.observed_difficulty(times_served=4, times_correct=1) is None
    assert scoring.observed_difficulty(times_served=40, times_correct=10) == pytest.approx(0.75)


def test_observed_difficulty_maps_back_onto_the_authored_vocabulary() -> None:
    assert scoring.difficulty_band(0.80) == "hard"
    assert scoring.difficulty_band(0.50) == "medium"
    assert scoring.difficulty_band(0.10) == "easy"
