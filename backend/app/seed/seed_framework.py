"""Seed the competency framework.

Framework version, competencies with their embeddings, job roles, activities,
the expectation matrix and SME cut-scores.

Idempotent throughout. Every write is an upsert on a natural key, and the
expectation matrix is declarative: a competency removed from a role disappears
from that role, rather than lingering as a stale requirement in an officer's
gap list long after it stopped being part of the job.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import embeddings
from app.core.logging import get_logger
from app.models.architecture import (
    Activity,
    ActivityCompetency,
    CompetencyCutScore,
    FrameworkVersion,
)
from app.models.competency import Competency, RoleCompetencyRequirement
from app.models.user import JobRole
from app.seed.competencies_data import COMPETENCIES
from app.seed.framework_data import (
    ACTIVITIES,
    CUT_SCORES,
    FRAMEWORK_NOTES,
    FRAMEWORK_TITLE,
    FRAMEWORK_VERSION,
    JOB_ROLES,
    REQUIREMENTS,
)

log = get_logger(__name__)


async def seed_framework_version(session: AsyncSession) -> FrameworkVersion:
    """Create the framework version, sealed.

    Sealing is what makes a past dashboard reproducible. A sealed version is
    never edited; a change means a new version and a re-embedding pass.
    """
    existing = await session.scalar(
        select(FrameworkVersion).where(FrameworkVersion.version == FRAMEWORK_VERSION)
    )
    if existing is not None:
        return existing

    version = FrameworkVersion(
        version=FRAMEWORK_VERSION,
        title=FRAMEWORK_TITLE,
        notes=FRAMEWORK_NOTES,
        sealed=True,
        sealed_at=func.now(),
    )
    session.add(version)
    await session.flush()
    log.info("sealed framework version %s", FRAMEWORK_VERSION)
    return version


async def seed_competencies(session: AsyncSession) -> dict[str, Competency]:
    """Upsert the competency list and recompute embeddings.

    The embedding is built from name plus description, matching what the
    recommender embeds at query time, so the two live in the same space.
    """
    texts = [f"{c['name']}. {c['description']}" for c in COMPETENCIES]
    vectors = embeddings.embed_many(texts)

    for spec, vector in zip(COMPETENCIES, vectors):
        values = {
            "code": spec["code"],
            "name": spec["name"],
            "cluster": spec["cluster"],
            "description": spec["description"],
            "frac_type": spec["frac_type"],
            "kind": spec.get("kind", "skill"),
            "decay": spec.get("decay", "methodology"),
            "embedding": vector,
        }
        await session.execute(
            pg_insert(Competency)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[Competency.code],
                set_={k: v for k, v in values.items() if k != "code"},
            )
        )

    await session.flush()
    rows = (await session.execute(select(Competency))).scalars().all()
    by_code = {c.code: c for c in rows}
    log.info("seeded %d competencies (embeddings computed)", len(by_code))
    return by_code


async def seed_job_roles(session: AsyncSession) -> dict[str, JobRole]:
    for spec in JOB_ROLES:
        await session.execute(
            pg_insert(JobRole)
            .values(
                code=spec["code"],
                title=spec["title"],
                cadre=spec["cadre"],
                description=spec["description"],
            )
            .on_conflict_do_update(
                index_elements=[JobRole.code],
                set_={
                    "title": spec["title"],
                    "cadre": spec["cadre"],
                    "description": spec["description"],
                },
            )
        )

    await session.flush()
    rows = (await session.execute(select(JobRole))).scalars().all()
    by_code = {r.code: r for r in rows}
    log.info("seeded %d job roles", len(by_code))
    return by_code


async def seed_activities(
    session: AsyncSession,
    roles: dict[str, JobRole],
    competencies: dict[str, Competency],
) -> int:
    """Seed the Activity layer and its competency attachments.

    Position -> Role -> Activity -> Competency. This is the layer that lets a
    gap be explained as "you cannot yet do this part of your job".
    """
    count = 0
    for role_code, activities in ACTIVITIES.items():
        role = roles.get(role_code)
        if role is None:
            continue

        for sequence, spec in enumerate(activities, start=1):
            await session.execute(
                pg_insert(Activity)
                .values(
                    job_role_id=role.id,
                    code=spec["code"],
                    name=spec["name"],
                    description=spec.get("description"),
                    sequence=sequence,
                )
                .on_conflict_do_update(
                    index_elements=[Activity.job_role_id, Activity.code],
                    set_={
                        "name": spec["name"],
                        "description": spec.get("description"),
                        "sequence": sequence,
                    },
                )
            )
            await session.flush()

            activity = await session.scalar(
                select(Activity)
                .where(Activity.job_role_id == role.id)
                .where(Activity.code == spec["code"])
            )
            if activity is None:
                continue

            for comp_code, level in dict(spec["competencies"]).items():  # type: ignore[arg-type]
                competency = competencies.get(str(comp_code))
                if competency is None:
                    log.warning(
                        "activity %s references unknown competency %s",
                        spec["code"],
                        comp_code,
                    )
                    continue
                await session.execute(
                    pg_insert(ActivityCompetency)
                    .values(
                        activity_id=activity.id,
                        competency_id=competency.id,
                        required_level=int(level),
                    )
                    .on_conflict_do_update(
                        index_elements=[
                            ActivityCompetency.activity_id,
                            ActivityCompetency.competency_id,
                        ],
                        set_={"required_level": int(level)},
                    )
                )
            count += 1

    await session.flush()
    log.info("seeded %d activities", count)
    return count


async def seed_requirements(
    session: AsyncSession,
    roles: dict[str, JobRole],
    competencies: dict[str, Competency],
    version: FrameworkVersion,
) -> int:
    count = 0
    removed = 0

    for role_code, matrix in REQUIREMENTS.items():
        role = roles[role_code]
        for comp_code, (level, criticality, horizon) in matrix.items():
            competency = competencies[comp_code]
            values = {
                "job_role_id": role.id,
                "competency_id": competency.id,
                "required_level": level,
                "criticality": Decimal(criticality),
                "horizon": horizon,
                "framework_version_id": version.id,
            }
            await session.execute(
                pg_insert(RoleCompetencyRequirement)
                .values(**values)
                .on_conflict_do_update(
                    index_elements=[
                        RoleCompetencyRequirement.job_role_id,
                        RoleCompetencyRequirement.competency_id,
                    ],
                    set_={
                        k: v
                        for k, v in values.items()
                        if k not in ("job_role_id", "competency_id")
                    },
                )
            )
            count += 1

        # Declarative: a competency removed from a role must disappear from it,
        # or a stale requirement keeps surfacing in the officer's gap list.
        wanted = {competencies[code].id for code in matrix}
        stale = await session.execute(
            select(RoleCompetencyRequirement).where(
                RoleCompetencyRequirement.job_role_id == role.id,
                RoleCompetencyRequirement.competency_id.notin_(wanted),
            )
        )
        for row in stale.scalars().all():
            await session.delete(row)
            removed += 1

    await session.flush()
    log.info("seeded %d requirements (%d stale removed)", count, removed)
    return count


async def seed_cut_scores(
    session: AsyncSession, competencies: dict[str, Competency]
) -> int:
    """SME cut-scores, where a panel has set them.

    Competencies without an entry use the platform defaults. The point is that
    the boundaries are per competency and owned by people, not a global 70%.
    """
    count = 0
    for code, (l1, l2, l3, l4) in CUT_SCORES.items():
        competency = competencies.get(code)
        if competency is None:
            continue
        values = {
            "competency_id": competency.id,
            "level_1_min": Decimal(str(l1)),
            "level_2_min": Decimal(str(l2)),
            "level_3_min": Decimal(str(l3)),
            "level_4_min": Decimal(str(l4)),
            "method": "modified_angoff",
        }
        await session.execute(
            pg_insert(CompetencyCutScore)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[CompetencyCutScore.competency_id],
                set_={k: v for k, v in values.items() if k != "competency_id"},
            )
        )
        count += 1

    await session.flush()
    log.info("seeded %d SME cut-score sets", count)
    return count


async def seed_framework(session: AsyncSession) -> dict[str, object]:
    version = await seed_framework_version(session)
    competencies = await seed_competencies(session)
    roles = await seed_job_roles(session)
    activities = await seed_activities(session, roles, competencies)
    requirements = await seed_requirements(session, roles, competencies, version)
    cut_scores = await seed_cut_scores(session, competencies)

    return {
        "framework_version": version.version,
        "competencies": len(competencies),
        "job_roles": len(roles),
        "activities": activities,
        "requirements": requirements,
        "cut_scores": cut_scores,
    }
