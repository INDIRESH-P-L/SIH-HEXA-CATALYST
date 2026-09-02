"""M3 · scoring and competency update — pure functions.

Measurement layer. No language model touches anything in this file.

The scorer is a pure function of (responses, item metadata, cut-scores).
Re-running it on stored responses must reproduce the number exactly — that is
the audit test, and it is why nothing here reads a clock, a database or a
random seed.

The language model reads the response pattern *after* scoring to name a
misconception. It never produces or adjusts the number, because a competency
score feeds nomination and posting decisions and must be defensible by anyone
holding the scoring rule.

Scoring
-------
    score = 100 × Σ(wᵢ · cᵢ) / Σ(wᵢ)      w: easy 1, medium 2, hard 3
                                            c = 1 if correct, else 0
                                            Σ runs over every item ATTEMPTED

Worked example — easy 3/4, medium 2/3, hard 1/3:

    numerator   = (1×3) + (2×2) + (3×1) = 10
    denominator = (1×4) + (2×3) + (3×3) = 19
    score       = 52.6 %

The same paper reads 60 % unweighted. The weighting correctly penalises
failure on the items that discriminate.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

#: Difficulty weights. The whole point of the weighting is that failing a hard
#: item costs more than failing an easy one.
DIFFICULTY_WEIGHT: dict[str, int] = {"easy": 1, "medium": 2, "hard": 3}
DEFAULT_WEIGHT = 2

#: Below this many items an assessment is not treated as evidence of a level.
#: A three-question quiz that happens to go well says very little.
MIN_ITEMS_FOR_LEVEL_CHANGE = 5

#: FRAC is a four-point scale.
MAX_LEVEL = 4

#: Evidence confidence by delivery mode. Practice attempts are recorded but
#: stay out of administrator dashboards.
CONFIDENCE_BY_MODE: dict[str, float] = {"proctored": 0.90, "practice": 0.50}


@dataclass(frozen=True)
class CutScores:
    """SME-set band boundaries for one competency.

    Set per competency by a subject-matter panel using modified Angoff, never
    as one global threshold: 60 % on sampling theory and 60 % on spreadsheet
    hygiene are not the same statement about an officer.
    """

    level_1_min: float = 40.0
    level_2_min: float = 60.0
    level_3_min: float = 78.0
    level_4_min: float = 90.0

    def level_for(self, score: float) -> int:
        """Map a weighted score onto the FRAC scale."""
        if score >= self.level_4_min:
            return 4
        if score >= self.level_3_min:
            return 3
        if score >= self.level_2_min:
            return 2
        if score >= self.level_1_min:
            return 1
        return 0

    def as_dict(self) -> dict[str, float]:
        return {
            "level_1_min": self.level_1_min,
            "level_2_min": self.level_2_min,
            "level_3_min": self.level_3_min,
            "level_4_min": self.level_4_min,
        }


DEFAULT_CUT_SCORES = CutScores()


@dataclass(frozen=True)
class AnsweredQuestion:
    """One answered item, as the scorer sees it."""

    question_id: str
    correct_index: int
    selected_index: int | None
    difficulty: str = "medium"
    topic: str | None = None

    @property
    def attempted(self) -> bool:
        """Only attempted items enter the denominator."""
        return self.selected_index is not None

    @property
    def is_correct(self) -> bool:
        return self.selected_index is not None and self.selected_index == self.correct_index

    @property
    def weight(self) -> int:
        return DIFFICULTY_WEIGHT.get(self.difficulty, DEFAULT_WEIGHT)


@dataclass(frozen=True)
class ScoreBreakdown:
    """The arithmetic behind a score, reproducible from stored responses."""

    weighted_score: float
    raw_score: float
    numerator: int
    denominator: int
    attempted: int
    correct: int
    total_items: int
    per_difficulty: dict[str, tuple[int, int]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "weighted_score": self.weighted_score,
            "raw_score": self.raw_score,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "attempted": self.attempted,
            "correct": self.correct,
            "total_items": self.total_items,
            "weights": dict(DIFFICULTY_WEIGHT),
            "per_difficulty": {
                k: {"correct": c, "attempted": a} for k, (c, a) in self.per_difficulty.items()
            },
            "formula": "100 x sum(w_i * c_i) / sum(w_i) over items attempted",
        }


def score_assessment(answers: list[AnsweredQuestion]) -> ScoreBreakdown:
    """Difficulty-weighted score. Deterministic. No language model, ever.

    Unattempted items are excluded from both numerator and denominator, so
    abandoning an assessment does not silently deflate the score of the items
    that were answered. The attempted count travels with the result, which is
    what makes a partial attempt distinguishable from a complete one.
    """
    attempted = [a for a in answers if a.attempted]

    numerator = sum(a.weight for a in attempted if a.is_correct)
    denominator = sum(a.weight for a in attempted)
    correct = sum(1 for a in attempted if a.is_correct)

    per_difficulty: dict[str, tuple[int, int]] = {}
    for difficulty in DIFFICULTY_WEIGHT:
        bucket = [a for a in attempted if a.difficulty == difficulty]
        if bucket:
            per_difficulty[difficulty] = (sum(1 for a in bucket if a.is_correct), len(bucket))

    weighted = round(100 * numerator / denominator, 2) if denominator else 0.0
    raw = round(100 * correct / len(attempted), 2) if attempted else 0.0

    return ScoreBreakdown(
        weighted_score=weighted,
        raw_score=raw,
        numerator=numerator,
        denominator=denominator,
        attempted=len(attempted),
        correct=correct,
        total_items=len(answers),
        per_difficulty=per_difficulty,
    )


def count_correct(answers: list[AnsweredQuestion]) -> int:
    return sum(1 for a in answers if a.is_correct)


def next_level(
    current: int,
    score: float,
    n_attempted: int,
    cut_scores: CutScores = DEFAULT_CUT_SCORES,
) -> int:
    """The competency level after an assessment.

    The measured level comes from the SME cut-scores, not from an increment
    rule: an assessment measures where an officer *is*, and if they demonstrate
    level 3 they are recorded at level 3.

    Two guards remain:

      * below the minimum item count nothing changes — too few responses to be
        meaningful;
      * the level never decreases. A poor result sets a revisit flag and keeps
        the competency in the gap list, rather than demoting the officer on one
        bad afternoon. Decay handles genuine loss of currency, and it does so
        by lowering confidence rather than by rewriting history.
    """
    if n_attempted < MIN_ITEMS_FOR_LEVEL_CHANGE:
        return current
    measured = cut_scores.level_for(score)
    return min(max(current, measured), MAX_LEVEL)


def needs_revisit(score: float, cut_scores: CutScores = DEFAULT_CUT_SCORES) -> bool:
    """Whether the officer should be steered back to this competency."""
    return score < cut_scores.level_2_min


def confidence_for_mode(mode: str) -> float:
    return CONFIDENCE_BY_MODE.get(mode, CONFIDENCE_BY_MODE["practice"])


def weak_topics(answers: list[AnsweredQuestion], *, limit: int = 3) -> list[str]:
    """Topics answered incorrectly most often, worst first.

    A frequency count over the topics attached to wrong answers, weighted by
    difficulty so a missed hard item counts for more. The language model is
    later asked to write prose *about* this list; it never produces the list.
    Ties break alphabetically so the output is stable.
    """
    counter: Counter[str] = Counter()
    for a in answers:
        if a.attempted and not a.is_correct and a.topic and a.topic.strip():
            counter[a.topic.strip()] += a.weight
    ranked = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    return [topic for topic, _score in ranked[:limit]]


def strong_topics(answers: list[AnsweredQuestion], *, limit: int = 3) -> list[str]:
    """Topics answered correctly and never missed."""
    wrong = {
        a.topic.strip()
        for a in answers
        if a.attempted and not a.is_correct and a.topic and a.topic.strip()
    }
    counter: Counter[str] = Counter()
    for a in answers:
        if a.is_correct and a.topic and a.topic.strip() and a.topic.strip() not in wrong:
            counter[a.topic.strip()] += a.weight
    ranked = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    return [topic for topic, _score in ranked[:limit]]


# ── item calibration ─────────────────────────────────────────────────────────
#
# Launch is weighted classical test theory: transparent and works on day one.
# Elo runs in shadow, learning item difficulty from live responses. Two-
# parameter IRT becomes viable at roughly 200 responses per item.

#: How fast an item's difficulty moves per observation.
ELO_ITEM_K = 0.05
#: How fast an ability estimate moves per response.
ELO_ABILITY_K = 0.20


def expected_correct(ability: float, difficulty: float) -> float:
    """Probability a given ability answers a given difficulty correctly."""
    return 1.0 / (1.0 + pow(10.0, difficulty - ability))


def update_ability(ability: float, difficulty: float, correct: bool) -> float:
    """Elo ability update, applied per response."""
    expected = expected_correct(ability, difficulty)
    return round(ability + ELO_ABILITY_K * ((1.0 if correct else 0.0) - expected), 4)


def update_item_difficulty(difficulty: float, ability: float, correct: bool) -> float:
    """Elo difficulty update: an item that strong candidates miss gets harder."""
    expected = expected_correct(ability, difficulty)
    return round(difficulty + ELO_ITEM_K * (expected - (1.0 if correct else 0.0)), 4)


def observed_difficulty(times_served: int, times_correct: int) -> float | None:
    """Proportion incorrect, once an item has been served often enough.

    Returns ``None`` below the threshold rather than a noisy estimate, because
    replacing an authored difficulty with a number derived from four responses
    is worse than leaving it alone.
    """
    if times_served < 20:
        return None
    return round(1.0 - (times_correct / times_served), 4)


def difficulty_band(p_incorrect: float) -> str:
    """Map an observed difficulty back onto the authored vocabulary."""
    if p_incorrect >= 0.65:
        return "hard"
    if p_incorrect >= 0.35:
        return "medium"
    return "easy"
