"""M2 · competency framework services.

Foundation layer. Mirrors the FRAC model iGOT already uses — Position → Role →
Activity → Competency — and produces the expectation matrix and the competency
embedding index.

Database access lives here. The gap engine in ``m4_gap_engine`` never imports
SQLAlchemy: everything it needs is loaded in this module and handed to it as
plain dataclasses. That separation is what makes the gap arithmetic testable
without a database.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models.architecture import (
    Activity,
    ActivityCompetency,
    CompetencyCutScore,
    FrameworkVersion,
)
from app.models.competency import Competency, RoleCompetencyRequirement
from app.models.evidence import CONFIDENCE_BY_SOURCE, CompetencyEvidence, UserCompetency
from app.models.user import JobRole, Profile
from app.services.m3_scoring import CutScores
from app.services.m4_gap_engine import Observation, Requirement


# ── framework versions ───────────────────────────────────────────────────────


async def current_framework_version(session: AsyncSession) -> FrameworkVersion | None:
    """The most recently sealed version, or the newest draft if none is sealed."""
    sealed = await session.scalar(
        select(FrameworkVersion)
        .where(FrameworkVersion.sealed.is_(True))
        .order_by(FrameworkVersion.sealed_at.desc())
        .limit(1)
    )
    if sealed is not None:
        return sealed
    return await session.scalar(
        select(FrameworkVersion).order_by(FrameworkVersion.created_at.desc()).limit(1)
    )


async def list_framework_versions(session: AsyncSession) -> list[FrameworkVersion]:
    return list(
        (
            await session.execute(
                select(FrameworkVersion).order_by(FrameworkVersion.created_at.desc())
            )
        )
        .scalars()
        .all()
    )


async def seal_framework_version(
    session: AsyncSession, version_id: uuid.UUID
) -> FrameworkVersion:
    """Freeze a version. Sealing triggers re-embedding and is irreversible.

    A sealed version is what makes a past dashboard reproducible; unsealing one
    would silently rewrite history, so the operation does not exist.
    """
    version = await session.get(FrameworkVersion, version_id)
    if version is None:
        raise NotFoundError("No such framework version.")
    if version.sealed:
        raise ConflictError("That framework version is already sealed.")

    from sqlalchemy import func

    version.sealed = True
    version.sealed_at = func.now()
    await session.flush()
    return version


# ── competencies ─────────────────────────────────────────────────────────────


async def list_competencies(
    session: AsyncSession, cluster: str | None = None
) -> list[Competency]:
    stmt = select(Competency).order_by(Competency.cluster, Competency.name)
    if cluster:
        stmt = stmt.where(Competency.cluster == cluster)
    return list((await session.execute(stmt)).scalars().all())


async def get_competency(session: AsyncSession, competency_id: uuid.UUID) -> Competency:
    competency = await session.get(Competency, competency_id)
    if competency is None:
        raise NotFoundError("No such competency.")
    return competency


async def get_competency_by_code(session: AsyncSession, code: str) -> Competency:
    competency = await session.scalar(select(Competency).where(Competency.code == code))
    if competency is None:
        raise NotFoundError(f"No competency with code {code}.")
    return competency


async def load_cut_scores(session: AsyncSession, competency_id: uuid.UUID) -> CutScores:
    """SME cut-scores for one competency, or the defaults if none are set."""
    row = await session.get(CompetencyCutScore, competency_id)
    if row is None:
        return CutScores()
    return CutScores(
        level_1_min=float(row.level_1_min),
        level_2_min=float(row.level_2_min),
        level_3_min=float(row.level_3_min),
        level_4_min=float(row.level_4_min),
    )


# ── job roles and activities ─────────────────────────────────────────────────


async def list_job_roles(session: AsyncSession) -> list[JobRole]:
    return list(
        (await session.execute(select(JobRole).order_by(JobRole.title))).scalars().all()
    )


async def get_job_role(session: AsyncSession, job_role_id: uuid.UUID) -> JobRole:
    role = await session.get(JobRole, job_role_id)
    if role is None:
        raise NotFoundError("No such job role.")
    return role


async def get_job_role_by_code(session: AsyncSession, code: str) -> JobRole:
    role = await session.scalar(select(JobRole).where(JobRole.code == code))
    if role is None:
        raise NotFoundError(f"No job role with code {code}.")
    return role


async def load_activities(
    session: AsyncSession, job_role_id: uuid.UUID
) -> list[Activity]:
    """The concrete actions a role performs, in sequence.

    Activities are what let a gap be explained as "you cannot yet do this part
    of your job" rather than as an abstract score.
    """
    return list(
        (
            await session.execute(
                select(Activity)
                .where(Activity.job_role_id == job_role_id)
                .order_by(Activity.sequence, Activity.name)
            )
        )
        .scalars()
        .all()
    )


async def activities_for_competency(
    session: AsyncSession, job_role_id: uuid.UUID, competency_id: uuid.UUID
) -> list[Activity]:
    """Which activities of this role depend on this competency.

    This is the derivation shown next to a gap: not "you need SQL at level 3",
    but "three of your activities require it".
    """
    rows = await session.execute(
        select(Activity)
        .join(ActivityCompetency, ActivityCompetency.activity_id == Activity.id)
        .where(Activity.job_role_id == job_role_id)
        .where(ActivityCompetency.competency_id == competency_id)
        .order_by(Activity.sequence)
    )
    return list(rows.scalars().all())


# ── the expectation matrix ───────────────────────────────────────────────────


async def load_requirements(
    session: AsyncSession, job_role_id: uuid.UUID
) -> list[tuple[RoleCompetencyRequirement, Competency]]:
    stmt = (
        select(RoleCompetencyRequirement, Competency)
        .join(Competency, Competency.id == RoleCompetencyRequirement.competency_id)
        .where(RoleCompetencyRequirement.job_role_id == job_role_id)
        .order_by(Competency.cluster, Competency.name)
    )
    return [tuple(row) for row in (await session.execute(stmt)).all()]  # type: ignore[misc]


async def load_requirement_specs(
    session: AsyncSession,
    job_role_id: uuid.UUID,
    *,
    assessed_version_id: uuid.UUID | None = None,
) -> list[Requirement]:
    """Requirements as plain dataclasses the pure gap engine can consume.

    ``assessed_version_id`` is the framework version the officer was last
    assessed against. Requirements introduced after it are flagged as new,
    which is how an emerging gap is identified — by diffing sealed versions,
    not by forecasting.
    """
    rows = await load_requirements(session, job_role_id)
    return [
        Requirement(
            competency_id=str(competency.id),
            competency_code=competency.code,
            competency_name=competency.name,
            cluster=competency.cluster,
            required_level=requirement.required_level,
            criticality=float(requirement.criticality),
            horizon=requirement.horizon,
            competency_description=competency.description,
            decay=competency.decay,
            is_new_in_version=(
                assessed_version_id is not None
                and requirement.framework_version_id is not None
                and requirement.framework_version_id != assessed_version_id
            ),
        )
        for requirement, competency in rows
    ]


# ── the evidence ledger ──────────────────────────────────────────────────────


async def load_observations(
    session: AsyncSession, user_id: uuid.UUID
) -> dict[str, Observation]:
    """The strongest evidence on file per competency, keyed by competency id.

    Reads the ``user_competency`` view, which is the latest evidence row per
    (user, competency). Competencies with no evidence are simply absent; the
    gap engine treats a missing entry as level 0 at low confidence.
    """
    rows = (
        await session.execute(
            select(
                UserCompetency.competency_id,
                UserCompetency.current_level,
                UserCompetency.confidence,
                UserCompetency.source_type,
                UserCompetency.assessed_at,
            ).where(UserCompetency.user_id == user_id)
        )
    ).all()
    return {
        str(competency_id): Observation(
            level=int(level),
            confidence=float(confidence),
            source_type=source_type,
            assessed_at=assessed_at,
        )
        for competency_id, level, confidence, source_type, assessed_at in rows
    }


async def load_current_levels(
    session: AsyncSession, user_id: uuid.UUID
) -> dict[str, int]:
    """Current level per competency id."""
    return {key: obs.level for key, obs in (await load_observations(session, user_id)).items()}


async def load_current_levels_by_code(
    session: AsyncSession, user_id: uuid.UUID
) -> dict[str, int]:
    """Current level keyed by competency code, for prerequisite checks."""
    rows = (
        await session.execute(
            select(Competency.code, UserCompetency.current_level)
            .join(UserCompetency, UserCompetency.competency_id == Competency.id)
            .where(UserCompetency.user_id == user_id)
        )
    ).all()
    return {code: int(level) for code, level in rows}


async def load_competency_standing(
    session: AsyncSession, user_id: uuid.UUID
) -> list[UserCompetency]:
    return list(
        (
            await session.execute(
                select(UserCompetency)
                .where(UserCompetency.user_id == user_id)
                .order_by(UserCompetency.assessed_at.desc())
            )
        )
        .scalars()
        .all()
    )


async def has_evidence_on_file(session: AsyncSession, user_id: uuid.UUID) -> bool:
    """Whether this officer has ever declared or been assessed on anything.

    This is the durable answer to "has this officer been through onboarding?".
    The wizard's whole purpose is to write a first row into the ledger, so the
    presence of a row *is* the completion signal — and unlike a browser flag it
    survives a new device, a cleared cache and a second session, which matters
    because re-running the wizard would append fresh self-declarations that
    supersede real assessment evidence.
    """
    return (
        await session.scalar(
            select(CompetencyEvidence.id)
            .where(CompetencyEvidence.user_id == user_id)
            .limit(1)
        )
    ) is not None


async def declare_baseline(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    competency_id: uuid.UUID,
    level: int,
    note: str | None = None,
) -> CompetencyEvidence:
    """Record a self-declared level, at the confidence self-declaration warrants.

    Appends to the ledger rather than editing anything. An assessment result
    later supersedes it simply by being newer and more confident.
    """
    await get_competency(session, competency_id)

    evidence = CompetencyEvidence(
        user_id=user_id,
        competency_id=competency_id,
        level=level,
        source_type="self_declared",
        confidence=CONFIDENCE_BY_SOURCE["self_declared"],
        note=note or "Self-declared baseline.",
    )
    session.add(evidence)
    await session.flush()
    return evidence


async def record_evidence(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    competency_id: uuid.UUID,
    level: int,
    source_type: str,
    source_ref: uuid.UUID | None = None,
    score: Decimal | float | None = None,
    confidence: Decimal | float | None = None,
    note: str | None = None,
) -> CompetencyEvidence:
    """Append evidence of any kind.

    ``confidence`` may be given explicitly — a practice assessment writes 0.50
    where a proctored one writes 0.90 — and otherwise falls back to the value
    the source type warrants.
    """
    resolved = (
        Decimal(str(confidence))
        if confidence is not None
        else CONFIDENCE_BY_SOURCE.get(source_type, Decimal("0.50"))
    )
    evidence = CompetencyEvidence(
        user_id=user_id,
        competency_id=competency_id,
        level=level,
        score=Decimal(str(score)) if score is not None else None,
        source_type=source_type,
        source_ref=source_ref,
        confidence=resolved,
        note=note,
    )
    session.add(evidence)
    await session.flush()
    return evidence


async def resolve_job_role_for_user(
    session: AsyncSession, profile: Profile
) -> JobRole | None:
    if profile.job_role_id is None:
        return None
    return await session.get(JobRole, profile.job_role_id)
