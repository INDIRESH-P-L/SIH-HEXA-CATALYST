"""M4 · Skill Gap Engine — pure functions.

Decision layer. Expected minus current, weighted by criticality, confidence and
horizon. Every gap carries its derivation.

This module has no database imports, no FastAPI imports and no I/O of any kind.
Every function is a total function of its arguments. That is deliberate: gap
analysis is the part of the product most likely to be challenged, and being
able to unit-test it directly is what makes the answer defensible.

None of this is AI. It is arithmetic, and saying so plainly is a strength. No
language model computes or adjusts a gap, a band or a priority.

The priority formula
--------------------
    priority = (expected − current) × criticality × (2 − confidence) × horizon

The ``(2 − confidence)`` term is the one that matters. An unmeasured or stale
competency sits near 0.25 confidence, which nearly doubles its priority — the
engine surfaces "we do not know whether this officer can do this" as urgent,
which is the honest position and the one that drives people into assessment.

The FRAC scale
--------------
Four points, and the only scale used anywhere in the platform:

    1 Awareness · 2 Application · 3 Leveraging for decisions · 4 Subject Matter Expert

Level 0 is not part of FRAC. It means no evidence is on file, which is a
different statement from "the lowest rung" and is displayed differently.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Iterable

#: Level 0 means "no evidence on file", distinct from FRAC level 1.
NO_EVIDENCE_LEVEL = 0
MIN_LEVEL = 0
MAX_LEVEL = 4

#: iGOT Karmayogi's FRAC proficiency scale.
FRAC_LABELS: dict[int, str] = {
    0: "No evidence",
    1: "Awareness",
    2: "Application",
    3: "Leveraging for decisions",
    4: "Subject Matter Expert",
}

FRAC_SHORT: dict[int, str] = {
    0: "—",
    1: "Awareness",
    2: "Application",
    3: "Leveraging",
    4: "SME",
}

#: Criticality range on a requirement.
MIN_CRITICALITY = 1.0
MAX_CRITICALITY = 3.0

#: Horizon discount. A next-role requirement is real but not yet urgent.
HORIZON_WEIGHT: dict[str, float] = {"current_role": 1.0, "next_role": 0.6}

#: Below this, supporting evidence is treated as stale: priority rises and the
#: officer is nudged towards re-assessment.
STALE_CONFIDENCE = 0.4

#: Months after which evidence of each kind stops being trustworthy.
#: Behavioural competencies do not decay.
DECAY_MONTHS: dict[str, int | None] = {
    "tools_platforms": 18,
    "regulatory_procedural": 12,
    "methodology": 36,
    "behavioural": None,
}


class GapBand(StrEnum):
    """Classification of a single competency gap."""

    CRITICAL = "CRITICAL"        # 2+ levels below, high criticality
    SIGNIFICANT = "SIGNIFICANT"  # 1–2 levels below
    EMERGING = "EMERGING"        # new in this framework version, or next role
    MET = "MET"                  # at expectation
    STRENGTH = "STRENGTH"        # above expectation — candidate mentor


#: Criticality at or above which a two-level shortfall is CRITICAL rather than
#: merely SIGNIFICANT.
HIGH_CRITICALITY = 2.0


@dataclass(frozen=True)
class Requirement:
    """What a job role expects of one competency."""

    competency_id: str
    competency_code: str
    competency_name: str
    cluster: str
    required_level: int
    criticality: float = 1.0
    horizon: str = "current_role"
    competency_description: str = ""
    decay: str = "methodology"
    #: True when this requirement did not exist in the framework version the
    #: officer was last assessed against.
    is_new_in_version: bool = False


@dataclass(frozen=True)
class Observation:
    """The strongest evidence on file for one competency."""

    level: int = NO_EVIDENCE_LEVEL
    confidence: float = 0.25
    source_type: str | None = None
    assessed_at: datetime | None = None

    @property
    def has_evidence(self) -> bool:
        return self.source_type is not None


@dataclass(frozen=True)
class GapRow:
    """One line of the gap analysis, with its full derivation."""

    competency_id: str
    competency_code: str
    competency_name: str
    cluster: str
    required_level: int
    current_level: int
    gap: int
    band: GapBand
    priority: float
    criticality: float
    horizon: str
    confidence: float
    frac_current: str
    frac_required: str
    stale: bool
    source_type: str | None = None
    assessed_at: datetime | None = None
    competency_description: str = ""
    #: Every multiplier, so the interface can show the arithmetic.
    derivation: dict[str, float | str | bool] | None = None

    @property
    def is_met(self) -> bool:
        return self.gap == 0

    @property
    def needs_reassessment(self) -> bool:
        return self.stale or not self.source_type


@dataclass(frozen=True)
class GapSummary:
    """Counts per band and the worst few gaps."""

    total_competencies: int
    critical: int
    significant: int
    emerging: int
    met: int
    strength: int
    top_gaps: list[GapRow]
    average_current_level: float
    average_required_level: float
    stale_count: int
    unassessed_count: int

    @property
    def open_gaps(self) -> int:
        return self.critical + self.significant + self.emerging


# ── scale helpers ────────────────────────────────────────────────────────────


def clamp_level(level: int) -> int:
    """Keep a level inside the 0–4 scale."""
    return max(MIN_LEVEL, min(MAX_LEVEL, level))


def frac_label(level: int) -> str:
    """Human label for a proficiency level on the FRAC scale."""
    return FRAC_LABELS.get(clamp_level(level), FRAC_LABELS[NO_EVIDENCE_LEVEL])


def frac_short(level: int) -> str:
    return FRAC_SHORT.get(clamp_level(level), FRAC_SHORT[NO_EVIDENCE_LEVEL])


def horizon_weight(horizon: str) -> float:
    return HORIZON_WEIGHT.get(horizon, 1.0)


def is_stale(
    decay: str, assessed_at: datetime | None, *, now: datetime | None = None
) -> bool:
    """Whether evidence has aged past its decay class.

    Behavioural competencies do not decay; everything else does, on the class
    the framework assigns it.
    """
    months = DECAY_MONTHS.get(decay)
    if months is None or assessed_at is None:
        return False
    reference = now or datetime.now(tz=timezone.utc)
    if assessed_at.tzinfo is None:
        assessed_at = assessed_at.replace(tzinfo=timezone.utc)
    elapsed_months = (reference - assessed_at).days / 30.44
    return elapsed_months > months


# ── the arithmetic ───────────────────────────────────────────────────────────


def compute_gap(required_level: int, current_level: int) -> int:
    """Shortfall against the requirement. Never negative.

    Exceeding a requirement is not a negative gap — it is a strength. Allowing
    negatives would let a strong competency mathematically offset a weak one in
    any aggregate, which is exactly wrong for capacity planning.
    """
    return max(0, required_level - current_level)


def band_for(
    gap: int,
    *,
    criticality: float = 1.0,
    horizon: str = "current_role",
    current_level: int = 0,
    required_level: int = 0,
    is_new_in_version: bool = False,
) -> GapBand:
    """Classify a gap.

    CRITICAL is reserved for a shortfall of two or more levels in a competency
    the role marks as highly critical. A two-level shortfall in an incidental
    competency is SIGNIFICANT, not critical — otherwise the word stops meaning
    anything and every dashboard is red.
    """
    if current_level > required_level:
        return GapBand.STRENGTH
    if gap == 0:
        return GapBand.MET
    if is_new_in_version or horizon == "next_role":
        return GapBand.EMERGING
    if gap >= 2 and criticality >= HIGH_CRITICALITY:
        return GapBand.CRITICAL
    return GapBand.SIGNIFICANT


def priority_for(
    gap: int, criticality: float, confidence: float, horizon: str
) -> float:
    """Ranking weight for a gap.

        priority = gap × criticality × (2 − confidence) × horizon

    Confidence enters inverted on purpose. Evidence we are sure of contributes
    its face value; evidence we are unsure of — a self-declaration at 0.25, or
    anything stale — is amplified, because not knowing is itself a finding.
    """
    if gap <= 0:
        return 0.0
    uncertainty = 2.0 - max(0.0, min(1.0, confidence))
    return round(gap * float(criticality) * uncertainty * horizon_weight(horizon), 4)


def build_gap_row(
    requirement: Requirement,
    observation: Observation,
    *,
    now: datetime | None = None,
) -> GapRow:
    """Turn one requirement plus one observation into a gap row with its derivation."""
    current = clamp_level(observation.level)
    required = clamp_level(requirement.required_level)
    gap = compute_gap(required, current)

    stale = is_stale(requirement.decay, observation.assessed_at, now=now)
    # Stale evidence is treated as low-confidence regardless of how it was
    # originally obtained, which is what raises its priority.
    confidence = (
        min(observation.confidence, STALE_CONFIDENCE) if stale else observation.confidence
    )

    band = band_for(
        gap,
        criticality=requirement.criticality,
        horizon=requirement.horizon,
        current_level=current,
        required_level=required,
        is_new_in_version=requirement.is_new_in_version,
    )
    priority = priority_for(gap, requirement.criticality, confidence, requirement.horizon)

    return GapRow(
        competency_id=requirement.competency_id,
        competency_code=requirement.competency_code,
        competency_name=requirement.competency_name,
        cluster=requirement.cluster,
        required_level=required,
        current_level=current,
        gap=gap,
        band=band,
        priority=priority,
        criticality=float(requirement.criticality),
        horizon=requirement.horizon,
        confidence=round(confidence, 2),
        frac_current=frac_label(current),
        frac_required=frac_label(required),
        stale=stale,
        source_type=observation.source_type,
        assessed_at=observation.assessed_at,
        competency_description=requirement.competency_description,
        derivation={
            "expected": required,
            "current": current,
            "difference": gap,
            "criticality": round(float(requirement.criticality), 2),
            "confidence": round(confidence, 2),
            "uncertainty_multiplier": round(2.0 - confidence, 2),
            "horizon": requirement.horizon,
            "horizon_multiplier": horizon_weight(requirement.horizon),
            "stale": stale,
            "priority": priority,
            "formula": "(expected - current) x criticality x (2 - confidence) x horizon",
        },
    )


def build_gap_rows(
    requirements: Iterable[Requirement],
    observations: dict[str, Observation],
    *,
    now: datetime | None = None,
) -> list[GapRow]:
    """Compute the full gap analysis.

    A competency absent from ``observations`` has no evidence on file and is
    treated as level 0 at 0.25 confidence rather than being skipped — an
    unassessed critical competency is a finding, not a blank.

    Sorted by priority descending, then gap, then name, so the ordering is
    stable for a given input and does not shuffle between requests.
    """
    rows = [
        build_gap_row(
            requirement,
            observations.get(requirement.competency_id, Observation()),
            now=now,
        )
        for requirement in requirements
    ]
    rows.sort(key=lambda r: (-r.priority, -r.gap, r.competency_name))
    return rows


def summarise(rows: list[GapRow], *, top_n: int = 3) -> GapSummary:
    counts = {band: 0 for band in GapBand}
    for row in rows:
        counts[row.band] += 1

    total = len(rows)
    unmet = [r for r in rows if r.gap > 0]
    return GapSummary(
        total_competencies=total,
        critical=counts[GapBand.CRITICAL],
        significant=counts[GapBand.SIGNIFICANT],
        emerging=counts[GapBand.EMERGING],
        met=counts[GapBand.MET],
        strength=counts[GapBand.STRENGTH],
        top_gaps=unmet[:top_n],
        average_current_level=(
            round(sum(r.current_level for r in rows) / total, 2) if total else 0.0
        ),
        average_required_level=(
            round(sum(r.required_level for r in rows) / total, 2) if total else 0.0
        ),
        stale_count=sum(1 for r in rows if r.stale),
        unassessed_count=sum(1 for r in rows if not r.source_type),
    )


def target_gaps(rows: list[GapRow], *, limit: int = 5) -> list[GapRow]:
    """The gaps the recommender should aim at: unmet, worst first, capped."""
    return [r for r in rows if r.gap >= 1][:limit]


def reassessment_candidates(rows: list[GapRow]) -> list[GapRow]:
    """Competencies whose evidence is stale or missing entirely."""
    return [r for r in rows if r.needs_reassessment]


def prerequisites_satisfied(
    prerequisites: Iterable[str],
    levels_by_code: dict[str, int],
    *,
    min_level: int = 1,
) -> bool:
    """Whether an officer meets a course's stated prerequisites.

    A prerequisite is a competency code, met when the officer holds evidence at
    or above ``min_level``. An empty list is satisfied by definition.

    Deliberately permissive: a prototype that hides relevant courses behind a
    strict prerequisite check looks broken rather than careful.
    """
    return all(
        levels_by_code.get(code, NO_EVIDENCE_LEVEL) >= min_level for code in prerequisites
    )


def snapshot_key(user_id: str, framework_version: str, taken_on: date) -> str:
    """Identity of a stored gap snapshot."""
    return f"{user_id}:{framework_version}:{taken_on.isoformat()}"
