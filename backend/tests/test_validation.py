"""M8 · the validation gate.

One test per check, each with a deliberately faulty item, plus a clean item
that must pass everything. This is what backs the claim that generated
questions are filtered by rules rather than by another model.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.services.m8_generator import validate

SOURCE = (
    "GROUP BY divides rows into groups sharing the same value in the named "
    "columns and applies aggregate functions within each group separately. "
    "HAVING filters groups after aggregation, whereas WHERE filters rows "
    "before aggregation. An INNER JOIN returns only rows that have a match in "
    "both tables."
)


def good_item(**overrides: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "question_text": "Which clause filters grouped rows after aggregation has run?",
        "options": [
            "HAVING, because it applies to groups",
            "WHERE, because it applies to rows",
            "ORDER BY, because it sorts the output",
            "SELECT, because it chooses columns",
        ],
        "correct_index": 0,
        "explanation": "HAVING applies once groups exist, so it can test a computed group value.",
        "difficulty": "medium",
        "topic": "GROUP BY with HAVING",
    }
    item.update(overrides)
    return item


def run(item: dict[str, Any], **kwargs: Any) -> validate.ValidationResult:
    return validate.validate_item(item, source_chunk=SOURCE, **kwargs)


# ── the clean item ───────────────────────────────────────────────────────────


def test_a_sound_item_passes_all_ten_checks() -> None:
    result = run(good_item())
    assert result.passed, result.failure_reason()
    assert len(result.checks) == 10
    assert result.failed_checks == []


def test_every_named_check_is_reported() -> None:
    """The trainer's report shows all ten, passed or failed."""
    result = run(good_item())
    assert set(result.checks) == set(validate.CHECK_NAMES)


# ── 1 · option count ─────────────────────────────────────────────────────────


def test_rejects_wrong_number_of_options() -> None:
    result = run(good_item(options=["a", "b", "c"]))
    assert "option_count" in result.failed_checks


def test_rejects_an_empty_option() -> None:
    result = run(good_item(options=["HAVING", "   ", "ORDER BY", "SELECT"]))
    assert "option_count" in result.failed_checks


# ── 2 · option uniqueness ────────────────────────────────────────────────────


def test_rejects_duplicate_options_ignoring_case() -> None:
    result = run(
        good_item(
            options=[
                "HAVING, because it applies to groups",
                "having, BECAUSE it applies to groups",
                "ORDER BY, because it sorts the output",
                "SELECT, because it chooses columns",
            ]
        )
    )
    assert "option_uniqueness" in result.failed_checks


# ── 3 · key range ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("index", [-1, 4, 99])
def test_rejects_an_out_of_range_answer_key(index: int) -> None:
    assert "key_range" in run(good_item(correct_index=index)).failed_checks


# ── 4 · stem length ──────────────────────────────────────────────────────────


def test_rejects_a_stem_that_is_too_short() -> None:
    assert "stem_length" in run(good_item(question_text="Why?")).failed_checks


def test_rejects_a_stem_that_is_too_long() -> None:
    long_stem = "Which clause filters grouped rows after aggregation " * 10
    assert "stem_length" in run(good_item(question_text=long_stem)).failed_checks


# ── 5 · explanation ──────────────────────────────────────────────────────────


def test_rejects_a_stub_explanation() -> None:
    assert "explanation" in run(good_item(explanation="Correct.")).failed_checks


def test_rejects_an_explanation_that_only_restates_the_answer() -> None:
    result = run(
        good_item(
            explanation="HAVING, because it applies to groups",
        )
    )
    assert "explanation" in result.failed_checks


# ── 6 · banned options ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "banned",
    ["All of the above", "none of the above", "Both A and B", "All of these"],
)
def test_rejects_lazy_distractors(banned: str) -> None:
    result = run(
        good_item(
            options=[
                "HAVING, because it applies to groups",
                "WHERE, because it applies to rows",
                "ORDER BY, because it sorts the output",
                banned,
            ]
        )
    )
    assert "banned_options" in result.failed_checks


# ── 7 · length bias ──────────────────────────────────────────────────────────


def test_rejects_a_conspicuously_long_correct_option() -> None:
    result = run(
        good_item(
            options=[
                "HAVING, because it applies to groups once aggregation has produced them and a computed value exists to test",
                "WHERE",
                "ORDER BY",
                "SELECT",
            ]
        )
    )
    assert "length_bias" in result.failed_checks


def test_accepts_balanced_option_lengths() -> None:
    assert "length_bias" not in run(good_item()).failed_checks


# ── 8 · near-duplicate ───────────────────────────────────────────────────────


def test_rejects_a_near_duplicate_of_an_existing_item() -> None:
    vector = [0.1] * 384
    result = run(good_item(), embedding=vector, existing_embeddings=[vector])
    assert "near_duplicate" in result.failed_checks


def test_accepts_an_item_unlike_anything_in_the_bank() -> None:
    a = [1.0] + [0.0] * 383
    b = [0.0, 1.0] + [0.0] * 382
    result = run(good_item(), embedding=a, existing_embeddings=[b])
    assert "near_duplicate" not in result.failed_checks


def test_an_empty_bank_cannot_produce_a_duplicate() -> None:
    result = run(good_item(), embedding=[0.1] * 384, existing_embeddings=[])
    assert "near_duplicate" not in result.failed_checks


# ── 9 · difficulty ───────────────────────────────────────────────────────────


@pytest.mark.parametrize("value", ["", "trivial", "EXTREME", "5"])
def test_rejects_an_unrecognised_difficulty(value: str) -> None:
    assert "difficulty" in run(good_item(difficulty=value)).failed_checks


@pytest.mark.parametrize("value", ["easy", "medium", "hard"])
def test_accepts_the_three_valid_difficulties(value: str) -> None:
    assert "difficulty" not in run(good_item(difficulty=value)).failed_checks


# ── 10 · grounding ───────────────────────────────────────────────────────────


def test_rejects_a_question_the_passage_does_not_support() -> None:
    """The guard against a model answering from its own prior knowledge."""
    result = run(
        good_item(
            question_text="What is the capital city of France and when was it founded?"
        )
    )
    assert "grounding" in result.failed_checks


def test_accepts_a_question_written_from_the_passage() -> None:
    assert "grounding" not in run(good_item()).failed_checks


def test_grounding_tolerates_inflection() -> None:
    """'filters'/'filtering' and 'aggregate'/'aggregation' are the same term."""
    result = validate.check_grounding(
        "Which clause is filtering grouped rows once aggregate functions have run?",
        SOURCE,
    )
    assert result.passed, result.detail


def test_same_term_matching() -> None:
    assert validate.same_term("filter", "filters")
    assert validate.same_term("aggregate", "aggregation")
    assert validate.same_term("join", "joining")
    assert not validate.same_term("statement", "statistical")


# ── the report ───────────────────────────────────────────────────────────────


def test_failure_reason_names_the_checks_for_the_retry_prompt() -> None:
    result = run(good_item(difficulty="trivial", explanation="No."))
    reason = result.failure_reason()
    assert "Difficulty" in reason
    assert "Explanation" in reason


def test_result_serialises_for_storage_and_the_trainer_report() -> None:
    payload = run(good_item(difficulty="nope")).as_json()
    assert payload["passed"] is False
    assert "difficulty" in payload["failed_checks"]
    assert payload["checks"]["difficulty"]["passed"] is False
    assert len(payload["checks"]) == 10
