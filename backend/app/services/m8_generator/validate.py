"""The validation gate — deterministic, no language model involved.

A model wrote the question. Nothing here asks a model whether the question is
any good; every check is arithmetic, string comparison or vector distance.
That separation is the point: the interesting claim is not "an LLM generates
questions" but "generated questions are filtered by rules a human can read".

Ten checks (§11.4). An item passes only if all ten pass. Per-check results are
stored on the question and surfaced in the trainer's validation report.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.ai.embeddings import cosine_similarity

# ── Thresholds ───────────────────────────────────────────────────────────────

MIN_STEM_CHARS = 15
MAX_STEM_CHARS = 300
MIN_EXPLANATION_CHARS = 20

#: The correct option may not exceed the mean length of the distractors by more
#: than this. A conspicuously long right answer is guessable without knowing
#: the material.
MAX_LENGTH_BIAS = 0.40

#: Cosine similarity at or above this counts as a near-duplicate.
DUPLICATE_SIMILARITY = 0.95

#: Minimum stem content words that must also appear in the source passage.
MIN_GROUNDING_MATCHES = 3

BANNED_OPTION_PATTERNS = [
    re.compile(r"^\s*all\s+of\s+the\s+above", re.I),
    re.compile(r"^\s*none\s+of\s+the\s+above", re.I),
    re.compile(r"^\s*both\s+[a-d]\s+and\s+[a-d]", re.I),
    re.compile(r"^\s*(?:a|b|c|d)\s+and\s+(?:a|b|c|d)\s*$", re.I),
    re.compile(r"^\s*all\s+of\s+these", re.I),
    re.compile(r"^\s*none\s+of\s+these", re.I),
]

VALID_DIFFICULTIES = {"easy", "medium", "hard"}

#: Ignored when checking grounding: too common to evidence anything.
#:
#: Deliberately excludes words that double as technical keywords in the kind of
#: material this pipeline reads — WHERE, HAVING, BETWEEN, FROM, GROUP, ORDER and
#: so on. A general-purpose stopword list strips those, which made legitimate
#: questions about SQL clauses fail grounding for want of vocabulary.
STOPWORDS = frozenset(
    """
    about after again against all also among and any are because been before
    being but can cannot could did doing few for had has have here how its
    itself more must not now once only ought our ours own should some such than
    that the their theirs them then there these they this those through too
    until very was were when which while who whom why will with would you your
    yours whose following statement statements true false correct incorrect
    best least given above below option options answer
    """.split()
)

_WORD_RE = re.compile(r"[a-z][a-z0-9_\-]{2,}")

#: Two words of at least this length that share this many leading characters
#: are treated as the same term. This stands in for stemming: "filter",
#: "filters" and "filtering" share a prefix, as do "aggregate" and
#: "aggregation". A hand-rolled suffix stripper gets those inconsistently, and
#: an inconsistent stem is worse than none — it rejects fair questions.
GROUNDING_PREFIX = 5

#: The ten checks, in the order the report displays them.
CHECK_NAMES: tuple[str, ...] = (
    "option_count",
    "option_uniqueness",
    "key_range",
    "stem_length",
    "explanation",
    "banned_options",
    "length_bias",
    "near_duplicate",
    "difficulty",
    "grounding",
)

CHECK_LABELS: dict[str, str] = {
    "option_count": "Exactly four non-empty options",
    "option_uniqueness": "No two options identical",
    "key_range": "Answer key within 0-3",
    "stem_length": f"Stem {MIN_STEM_CHARS}-{MAX_STEM_CHARS} characters",
    "explanation": f"Explanation at least {MIN_EXPLANATION_CHARS} characters and not a restatement",
    "banned_options": "No 'all/none of the above' style options",
    "length_bias": f"Correct option not more than {int(MAX_LENGTH_BIAS * 100)}% longer than the mean distractor",
    "near_duplicate": f"Cosine similarity below {DUPLICATE_SIMILARITY} against the existing bank",
    "difficulty": "Difficulty is easy, medium or hard",
    "grounding": f"At least {MIN_GROUNDING_MATCHES} stem content words appear in the source passage",
}


@dataclass
class CheckOutcome:
    passed: bool
    detail: str = ""


@dataclass
class ValidationResult:
    """The verdict on one generated item."""

    passed: bool
    checks: dict[str, CheckOutcome] = field(default_factory=dict)

    @property
    def failed_checks(self) -> list[str]:
        return [name for name, outcome in self.checks.items() if not outcome.passed]

    def failure_reason(self) -> str:
        """One sentence naming what failed, used to prompt the single retry."""
        failures = [
            f"{CHECK_LABELS.get(name, name)} ({self.checks[name].detail})"
            for name in self.failed_checks
        ]
        return "; ".join(failures)

    def as_json(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "failed_checks": self.failed_checks,
            "checks": {
                name: {"passed": outcome.passed, "detail": outcome.detail or None}
                for name, outcome in self.checks.items()
            },
        }


def content_words(text: str) -> set[str]:
    """Lower-cased words of three or more letters, stopwords removed."""
    return {w for w in _WORD_RE.findall(text.lower()) if w not in STOPWORDS}


def same_term(a: str, b: str) -> bool:
    """Whether two content words denote the same term.

    Exact match, or a shared leading prefix long enough to survive inflection.
    Erring towards accepting is deliberate: this backs a check that exists to
    catch questions written from the model's own knowledge rather than from the
    passage, and a near-miss on word form is not that failure.
    """
    if a == b:
        return True
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    # One word is a whole prefix of the other: join/joining, column/columns.
    if len(shorter) >= 4 and longer.startswith(shorter):
        return True
    # Both long enough to share a stem: aggregate/aggregation, filter/filters.
    if len(a) < GROUNDING_PREFIX or len(b) < GROUNDING_PREFIX:
        return False
    return a[:GROUNDING_PREFIX] == b[:GROUNDING_PREFIX]


def grounding_overlap(stem: str, source: str) -> set[str]:
    """Stem content words that also occur in the source passage."""
    source_words = content_words(source)
    return {
        word
        for word in content_words(stem)
        if any(same_term(word, other) for other in source_words)
    }


# ── Individual checks ────────────────────────────────────────────────────────


def check_option_count(options: list[str]) -> CheckOutcome:
    if len(options) != 4:
        return CheckOutcome(False, f"got {len(options)} options")
    empty = [i for i, o in enumerate(options) if not o.strip()]
    if empty:
        return CheckOutcome(False, f"options {empty} are empty")
    return CheckOutcome(True)


def check_option_uniqueness(options: list[str]) -> CheckOutcome:
    normalised = [o.strip().lower() for o in options]
    if len(set(normalised)) != len(normalised):
        return CheckOutcome(False, "two options are the same")
    return CheckOutcome(True)


def check_key_range(correct_index: int, options: list[str]) -> CheckOutcome:
    if not isinstance(correct_index, int) or not 0 <= correct_index <= 3:
        return CheckOutcome(False, f"correct_index={correct_index}")
    if correct_index >= len(options):
        return CheckOutcome(False, f"correct_index={correct_index} exceeds option count")
    return CheckOutcome(True)


def check_stem_length(stem: str) -> CheckOutcome:
    length = len(stem.strip())
    if length < MIN_STEM_CHARS:
        return CheckOutcome(False, f"{length} characters, minimum {MIN_STEM_CHARS}")
    if length > MAX_STEM_CHARS:
        return CheckOutcome(False, f"{length} characters, maximum {MAX_STEM_CHARS}")
    return CheckOutcome(True)


def check_explanation(explanation: str, correct_option: str) -> CheckOutcome:
    text = explanation.strip()
    if len(text) < MIN_EXPLANATION_CHARS:
        return CheckOutcome(False, f"{len(text)} characters, minimum {MIN_EXPLANATION_CHARS}")
    if text.lower() == correct_option.strip().lower():
        return CheckOutcome(False, "restates the correct option verbatim")
    return CheckOutcome(True)


def check_banned_options(options: list[str]) -> CheckOutcome:
    for index, option in enumerate(options):
        for pattern in BANNED_OPTION_PATTERNS:
            if pattern.match(option.strip()):
                return CheckOutcome(False, f"option {index}: {option.strip()[:40]}")
    return CheckOutcome(True)


def check_length_bias(options: list[str], correct_index: int) -> CheckOutcome:
    """A conspicuously long correct option is a giveaway."""
    if len(options) != 4 or not 0 <= correct_index < len(options):
        return CheckOutcome(True, "skipped: option structure already invalid")

    correct_len = len(options[correct_index].strip())
    others = [len(o.strip()) for i, o in enumerate(options) if i != correct_index]
    mean_other = sum(others) / len(others) if others else 0
    if mean_other == 0:
        return CheckOutcome(True)

    ratio = (correct_len - mean_other) / mean_other
    if ratio > MAX_LENGTH_BIAS:
        return CheckOutcome(
            False,
            f"correct option {ratio * 100:.0f}% longer than the mean distractor",
        )
    return CheckOutcome(True)


def check_difficulty(difficulty: str) -> CheckOutcome:
    if str(difficulty).strip().lower() not in VALID_DIFFICULTIES:
        return CheckOutcome(False, f"got '{difficulty}'")
    return CheckOutcome(True)


def check_grounding(stem: str, source_chunk: str) -> CheckOutcome:
    """At least three content words of the stem must appear in the passage.

    A cheap, transparent guard against a model answering from its own prior
    knowledge instead of from the uploaded handout.
    """
    overlap = grounding_overlap(stem, source_chunk)
    if len(overlap) < MIN_GROUNDING_MATCHES:
        return CheckOutcome(
            False,
            f"only {len(overlap)} stem content words appear in the source passage",
        )
    return CheckOutcome(True, f"{len(overlap)} matching content words")


def check_near_duplicate(
    embedding: list[float] | None,
    existing_embeddings: list[list[float]],
) -> CheckOutcome:
    """Compare against the existing bank and the rest of the current batch."""
    if embedding is None or not existing_embeddings:
        return CheckOutcome(True, "no comparable items")

    best = 0.0
    for other in existing_embeddings:
        if len(other) != len(embedding):
            continue
        best = max(best, cosine_similarity(embedding, other))

    if best >= DUPLICATE_SIMILARITY:
        return CheckOutcome(False, f"cosine similarity {best:.3f} against an existing item")
    return CheckOutcome(True, f"closest existing item {best:.3f}")


# ── The gate ─────────────────────────────────────────────────────────────────


def validate_item(
    item: dict[str, Any],
    *,
    source_chunk: str,
    embedding: list[float] | None = None,
    existing_embeddings: list[list[float]] | None = None,
) -> ValidationResult:
    """Run all ten checks against one generated item."""
    stem = str(item.get("question_text", ""))
    options = [str(o) for o in (item.get("options") or [])]
    correct_index = item.get("correct_index", -1)
    explanation = str(item.get("explanation", ""))
    difficulty = str(item.get("difficulty", ""))

    correct_option = (
        options[correct_index]
        if isinstance(correct_index, int) and 0 <= correct_index < len(options)
        else ""
    )

    checks: dict[str, CheckOutcome] = {
        "option_count": check_option_count(options),
        "option_uniqueness": check_option_uniqueness(options),
        "key_range": check_key_range(correct_index, options),  # type: ignore[arg-type]
        "stem_length": check_stem_length(stem),
        "explanation": check_explanation(explanation, correct_option),
        "banned_options": check_banned_options(options),
        "length_bias": check_length_bias(options, correct_index),  # type: ignore[arg-type]
        "near_duplicate": check_near_duplicate(embedding, existing_embeddings or []),
        "difficulty": check_difficulty(difficulty),
        "grounding": check_grounding(stem, source_chunk),
    }

    return ValidationResult(
        passed=all(o.passed for o in checks.values()),
        checks={name: checks[name] for name in CHECK_NAMES},
    )
