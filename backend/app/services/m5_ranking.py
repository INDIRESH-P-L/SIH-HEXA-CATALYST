"""M5 · retrieval fusion, ranking and sequencing — pure functions.

Decision layer, split out from the database work so the parts that decide
*order* can be tested directly.

Three stages, and collapsing them into one similarity search is the common
mistake. It produces recommendations that are topically plausible and
operationally useless — a three-week residential programme proposed to an
officer with four hours a month, or an advanced module placed before its
prerequisite.

    STAGE 1  RETRIEVE   dense (pgvector) + lexical (BM25) + tag match,
                        ≈100 per gap, combined by reciprocal rank fusion
    STAGE 2  RANK       seven weighted terms, hard constraints, diversity cap
    STAGE 3  SEQUENCE   prerequisite DAG topological sort, calendar placement,
                        monthly hour budget

No language model participates in any of it. The model writes one explanatory
sentence per result, after the order is already fixed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Iterable, Sequence

# ── Stage 2 weights ──────────────────────────────────────────────────────────

WEIGHTS: dict[str, float] = {
    "gap_priority": 0.30,
    "semantic_similarity": 0.20,
    "level_fit": 0.15,
    "prerequisites_met": 0.10,
    "effort_fit": 0.10,
    "department_priority": 0.08,
    "recency_language": 0.07,
}

#: Reciprocal rank fusion constant. 60 is the value the IR literature settles
#: on; it damps the influence of any single ranker's top slot.
RRF_K = 60

#: FRAC is a four-point scale, so level fit is normalised over three steps.
LEVEL_SPAN = 3

#: Default monthly study budget for a serving officer, in hours.
DEFAULT_MONTHLY_HOURS = 8

#: At most this many offerings per competency, so one large gap cannot fill
#: the whole pathway.
MAX_PER_COMPETENCY = 2


@dataclass(frozen=True)
class RankedHit:
    """One retriever's opinion: an offering and where it placed."""

    course_id: str
    rank: int
    score: float = 0.0


@dataclass
class Offering:
    """A candidate, as the ranker sees it. No ORM types here."""

    course_id: str
    external_id: str
    source: str
    title: str
    competency_code: str
    proficiency_level: int
    duration_hours: int
    learning_format: str
    prerequisites: list[str] = field(default_factory=list)
    session_start: date | None = None
    seats: int | None = None
    language: str = "en"
    synced_days_ago: int = 0
    #: Set by the department, 0.0–1.0. Raises a competency the MDO is pushing.
    department_priority: float = 0.0


# ── Stage 1 · fusion ─────────────────────────────────────────────────────────


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[RankedHit]], *, k: int = RRF_K
) -> dict[str, float]:
    """Combine several rankings without needing their scores to be comparable.

    A dense retriever returns cosine similarity, BM25 returns a term-frequency
    score, and a tag match returns a boolean. Normalising those onto one axis
    requires assumptions that do not hold. Reciprocal rank fusion needs only
    the ordering, which is the part each retriever is actually good at.

        rrf(d) = Σ  1 / (k + rank(d))
    """
    fused: dict[str, float] = {}
    for ranking in rankings:
        for hit in ranking:
            fused[hit.course_id] = fused.get(hit.course_id, 0.0) + 1.0 / (k + hit.rank)
    return fused


def normalise_fusion(fused: dict[str, float]) -> dict[str, float]:
    """Scale fused scores onto 0–1 so they can act as one ranking term."""
    if not fused:
        return {}
    top = max(fused.values())
    if top <= 0:
        return {key: 0.0 for key in fused}
    return {key: value / top for key, value in fused.items()}


# ── Stage 2 · the ranking terms ──────────────────────────────────────────────


def level_fit(course_level: int, current_level: int) -> float:
    """How well a course level suits the officer's next step.

    1.0 when the course sits exactly one level above where they are, falling
    away linearly in both directions. Targeting current + 1 rather than the
    required level is the point: an officer at Awareness is not served by a
    Subject Matter Expert module, however well it matches the topic.
    """
    target = current_level + 1
    return max(0.0, 1.0 - abs(course_level - target) / LEVEL_SPAN)


def effort_fit(duration_hours: int, monthly_hours: int = DEFAULT_MONTHLY_HOURS) -> float:
    """Whether the officer can realistically absorb this.

    Anything inside one month's budget scores full marks. Beyond that the score
    decays with the number of months required, so a 40-hour residential
    programme is not ruled out — it is simply outranked by something the
    officer can finish, unless its other terms are strong enough.
    """
    if duration_hours <= 0:
        return 1.0
    budget = max(1, monthly_hours)
    months = duration_hours / budget
    if months <= 1.0:
        return 1.0
    return round(max(0.0, 1.0 / months), 4)


def recency_language_fit(
    synced_days_ago: int, language: str, preferred_language: str = "en"
) -> float:
    """Freshness of the catalogue record and whether the officer can read it.

    Combined into one term because neither justifies a weight of its own, and
    both describe the same thing: how usable this record is right now.
    """
    recency = 1.0 if synced_days_ago <= 30 else max(0.3, 1.0 - (synced_days_ago - 30) / 365)
    language_match = 1.0 if language == preferred_language else 0.6
    return round((recency + language_match) / 2, 4)


def format_effort_note(learning_format: str) -> float:
    """Self-paced study is easier to fit around duty than a dated programme."""
    return 1.0 if learning_format == "SELF_PACED" else 0.7


def score_offering(
    offering: Offering,
    *,
    gap_priority_normalised: float,
    similarity: float,
    current_level: int,
    prerequisites_met: bool,
    monthly_hours: int = DEFAULT_MONTHLY_HOURS,
    preferred_language: str = "en",
) -> tuple[float, dict[str, float]]:
    """Apply the seven-term formula. Returns (score, every term)."""
    terms = {
        "gap_priority": round(max(0.0, min(1.0, gap_priority_normalised)), 4),
        "semantic_similarity": round(max(0.0, min(1.0, similarity)), 4),
        "level_fit": round(level_fit(offering.proficiency_level, current_level), 4),
        "prerequisites_met": 1.0 if prerequisites_met else 0.0,
        "effort_fit": round(
            effort_fit(offering.duration_hours, monthly_hours)
            * format_effort_note(offering.learning_format),
            4,
        ),
        "department_priority": round(max(0.0, min(1.0, offering.department_priority)), 4),
        "recency_language": recency_language_fit(
            offering.synced_days_ago, offering.language, preferred_language
        ),
    }
    final = sum(WEIGHTS[name] * value for name, value in terms.items())
    return round(final, 4), terms


# ── Stage 2 · hard constraints and diversity ─────────────────────────────────


def apply_hard_constraints(
    offerings: Iterable[Offering],
    *,
    completed_ids: set[str],
    mandatory_ids: set[str] | None = None,
) -> tuple[list[Offering], list[Offering]]:
    """Split candidates into (pinned, rankable).

    Mandatory offerings are pinned to the top rather than competing on score:
    a compliance requirement is not a recommendation. Completed courses are
    removed outright.
    """
    mandatory = mandatory_ids or set()
    pinned: list[Offering] = []
    rankable: list[Offering] = []
    for offering in offerings:
        if offering.course_id in completed_ids:
            continue
        if offering.course_id in mandatory:
            pinned.append(offering)
        else:
            rankable.append(offering)
    return pinned, rankable


def cap_per_competency(
    scored: Sequence[tuple[float, Offering, str]],
    *,
    max_per_competency: int = MAX_PER_COMPETENCY,
) -> list[tuple[float, Offering, str]]:
    """Stop one large gap from filling the whole list.

    Input must arrive sorted by score, so keeping the first N per competency
    keeps the best ones.
    """
    seen: dict[str, int] = {}
    kept: list[tuple[float, Offering, str]] = []
    for entry in scored:
        code = entry[2]
        if seen.get(code, 0) >= max_per_competency:
            continue
        seen[code] = seen.get(code, 0) + 1
        kept.append(entry)
    return kept


# ── Stage 3 · sequencing ─────────────────────────────────────────────────────


def topological_order(
    offerings: Sequence[Offering], levels_by_code: dict[str, int]
) -> list[Offering]:
    """Order a pathway so prerequisites come before what depends on them.

    Edges are drawn only between offerings *inside this pathway*: a
    prerequisite the officer already holds is satisfied and creates no edge.
    Kahn's algorithm, with ties broken by proficiency level then title so the
    result is stable rather than merely valid. A cycle — which a malformed
    catalogue can produce — degrades to the original order rather than raising.
    """
    by_competency: dict[str, list[Offering]] = {}
    for offering in offerings:
        by_competency.setdefault(offering.competency_code, []).append(offering)

    indegree = {o.course_id: 0 for o in offerings}
    edges: dict[str, list[str]] = {o.course_id: [] for o in offerings}

    for offering in offerings:
        for prerequisite_code in offering.prerequisites:
            if levels_by_code.get(prerequisite_code, 0) >= 1:
                continue  # already held; not a constraint on this pathway
            for provider in by_competency.get(prerequisite_code, []):
                if provider.course_id == offering.course_id:
                    continue
                edges[provider.course_id].append(offering.course_id)
                indegree[offering.course_id] += 1

    lookup = {o.course_id: o for o in offerings}
    ready = sorted(
        [cid for cid, degree in indegree.items() if degree == 0],
        key=lambda cid: (lookup[cid].proficiency_level, lookup[cid].title),
    )

    ordered: list[Offering] = []
    while ready:
        current = ready.pop(0)
        ordered.append(lookup[current])
        for successor in edges[current]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(successor)
                ready.sort(key=lambda cid: (lookup[cid].proficiency_level, lookup[cid].title))

    if len(ordered) != len(offerings):
        # A cycle in the catalogue's prerequisite data. Emit what sorted, then
        # the remainder in their original order, rather than failing the whole
        # recommendation.
        placed = {o.course_id for o in ordered}
        ordered.extend(o for o in offerings if o.course_id not in placed)
    return ordered


@dataclass(frozen=True)
class PathwayStep:
    """One offering placed on the calendar."""

    order: int
    offering: Offering
    starts_on: date
    ends_on: date
    months_required: float
    anchored: bool  # True when a dated NSSTA session fixed the placement


def place_on_calendar(
    ordered: Sequence[Offering],
    *,
    start: date,
    monthly_hours: int = DEFAULT_MONTHLY_HOURS,
) -> list[PathwayStep]:
    """Lay a sequenced pathway onto a calendar against an hour budget.

    Dated NSSTA programmes are anchors: their session start is fixed and
    everything else flows around them. Self-paced iGOT courses fill the gaps,
    consuming the monthly budget.

    This is what turns a ranked list into something an officer can actually
    follow, and it is the stage most recommenders skip.
    """
    steps: list[PathwayStep] = []
    cursor = start
    budget = max(1, monthly_hours)

    for index, offering in enumerate(ordered, start=1):
        months = max(0.25, offering.duration_hours / budget)
        if offering.session_start is not None:
            # Dated programme: the academy decides when this happens.
            begins = offering.session_start
            anchored = True
        else:
            begins = cursor
            anchored = False
        ends = begins + timedelta(days=round(months * 30.44))
        steps.append(
            PathwayStep(
                order=index,
                offering=offering,
                starts_on=begins,
                ends_on=ends,
                months_required=round(months, 2),
                anchored=anchored,
            )
        )
        # A dated programme runs alongside self-paced study rather than
        # blocking it, so only unanchored steps advance the cursor.
        if not anchored:
            cursor = ends
    return steps


def pathway_total_hours(steps: Sequence[PathwayStep]) -> int:
    return sum(step.offering.duration_hours for step in steps)
