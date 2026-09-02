"""Seed the five demo users and their self-declared competency baselines.

Idempotent: users are matched on email, and a baseline is only written when the
officer has no evidence at all for that competency. That second rule matters —
re-running the seed after a demo must not overwrite the level a quiz produced,
because the evidence ledger is append-only and the latest row wins.

Runs only under AUTH_MODE=local. Under AUTH_MODE=supabase, identities live in
GoTrue and are created through POST /auth/register instead; the script says so
rather than silently doing nothing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.competency import Competency
from app.models.course import Course, Enrollment
from app.models.evidence import CONFIDENCE_BY_SOURCE, CompetencyEvidence
from app.models.user import AuthUser, JobRole, Profile, UserRole
from app.services.m1_identity.local_auth import hash_password

log = get_logger(__name__)

#: One shared password across the demo accounts. Local mode only; it never
#: reaches a Supabase deployment.
DEMO_PASSWORD = "Demo@2026"

DEMO_USERS: list[dict[str, object]] = [
    {
        "email": "priya.sharma@mospi.gov.in",
        "full_name": "Priya Sharma",
        "employee_code": "MOSPI/2021/0847",
        "designation": "Statistical Officer",
        "station": "New Delhi",
        "job_role_code": "STAT_OFFICER",
        "cadre": "ISS",
        "years_experience": 4,
        "education": "M.Sc. Statistics, Delhi University",
        "roles": ["employee"],
        # Engineered so SQL is the HIGH-gap demo subject: required 4, current 1.
        "baseline": {
            "SQL": 1,
            "PYTHON": 2,
            "SAMPLING": 3,
            "SURVEY_DESIGN": 3,
            "DATA_VIZ": 2,
            "GIS": 1,
            "PROJECT_MGMT": 2,
        },
    },
    {
        "email": "rakesh.nair@mospi.gov.in",
        "full_name": "Rakesh Nair",
        "employee_code": "MOSPI/2016/0312",
        "designation": "Senior Statistical Officer",
        "station": "Kolkata",
        "job_role_code": "SR_STAT_OFFICER",
        "cadre": "ISS",
        "years_experience": 9,
        "education": "M.Stat., Indian Statistical Institute",
        "roles": ["employee"],
        "baseline": {
            "SAMPLING": 4,
            "SURVEY_DESIGN": 4,
            "SQL": 3,
            "PYTHON": 3,
            "R_STATS": 3,
            "DATA_VIZ": 2,
            "DATA_PRIVACY": 2,
            "PROJECT_MGMT": 3,
        },
    },
    {
        "email": "meera.iyer@mospi.gov.in",
        "full_name": "Meera Iyer",
        "employee_code": "MOSPI/2009/0128",
        "designation": "Deputy Director",
        "station": "New Delhi",
        "job_role_code": "DEP_DIRECTOR",
        "cadre": "ISS",
        "years_experience": 16,
        "education": "Ph.D. Economics, Jawaharlal Nehru University",
        "roles": ["employee"],
        "baseline": {
            "NATIONAL_ACCOUNTS": 4,
            "PRICE_STATISTICS": 3,
            "SDG_INDICATORS": 3,
            "SAMPLING": 4,
            "SURVEY_DESIGN": 4,
            "DATA_PRIVACY": 3,
            "PROJECT_MGMT": 4,
            "CLOUD": 1,
        },
    },
    {
        "email": "anand.desai@nssta.gov.in",
        "full_name": "Anand Desai",
        "employee_code": "NSSTA/2014/0056",
        "designation": "Assistant Director (Training)",
        "station": "Greater Noida",
        "job_role_code": "SR_STAT_OFFICER",
        "cadre": "ISS",
        "years_experience": 11,
        "education": "M.Sc. Statistics, University of Pune",
        "roles": ["employee", "trainer"],
        "baseline": {},
    },
    {
        "email": "admin@mospi.gov.in",
        "full_name": "System Administrator",
        "employee_code": "MOSPI/ADMIN/0001",
        "designation": "Deputy Director (Systems)",
        "station": "New Delhi",
        "job_role_code": "DEP_DIRECTOR",
        "cadre": "ISS",
        "years_experience": 13,
        "education": "M.Tech. Computer Science, IIT Delhi",
        "roles": ["employee", "admin"],
        "baseline": {},
    },
    {
        "email": "vikram.rao@mospi.gov.in",
        "full_name": "Vikram Rao",
        "employee_code": "MOSPI/2019/0553",
        "designation": "Data Scientist (DIID)",
        "station": "New Delhi",
        "job_role_code": "DATA_SCIENTIST",
        "cadre": "OTHER",
        "years_experience": 6,
        "education": "M.Tech. Data Science, IIT Madras",
        "roles": ["employee"],
        "baseline": {
            "PYTHON": 4,
            "MACHINE_LEARNING": 3,
            "SQL": 4,
            "CLOUD": 2,
            "APIS": 2,
            "DATA_VIZ": 3,
            "R_STATS": 2,
            "CYBERSECURITY": 1,
            "DATA_PRIVACY": 2,
            "OPEN_DATA": 2,
        },
    },
    {
        "email": "sunita.devi@mospi.gov.in",
        "full_name": "Sunita Devi",
        "employee_code": "MOSPI/2013/0921",
        "designation": "Field Supervisor",
        "station": "Patna",
        "job_role_code": "FIELD_SUPERVISOR",
        "cadre": "SSS",
        "years_experience": 12,
        "education": "B.Sc. Statistics, Patna University",
        "roles": ["employee"],
        "baseline": {
            "SURVEY_DESIGN": 3,
            "SAMPLING": 2,
            "AGRI_STATISTICS": 3,
            "LABOUR_STATISTICS": 2,
            "DATA_QUALITY": 2,
            "GIS": 1,
            "PROJECT_MGMT": 3,
            "COMMUNICATION": 3,
            "CHANGE_MGMT": 1,
        },
    },
]


#: Previous trainings, as the problem statement calls them. Recorded as
#: completed enrolments plus course_completion evidence at confidence 0.60 —
#: stronger than self-declaration, weaker than a passed assessment.
#: They are also what makes the training-effectiveness report non-empty.
PRIOR_TRAINING: dict[str, list[tuple[str, str, int, int]]] = {
    # email -> [(external_id, competency_code, level_before, level_after)]
    "rakesh.nair@mospi.gov.in": [
        ("IGOT-R-201", "R_STATS", 2, 3),
        ("IGOT-VIZ-201", "DATA_VIZ", 1, 2),
    ],
    "meera.iyer@mospi.gov.in": [
        ("NSSTA-CPI-301", "PRICE_STATISTICS", 2, 3),
        ("IGOT-ETHICS-201", "ETHICS", 3, 4),
    ],
    "vikram.rao@mospi.gov.in": [
        ("IGOT-PY-301", "PYTHON", 3, 4),
        ("IGOT-ML-301", "MACHINE_LEARNING", 2, 3),
    ],
    "sunita.devi@mospi.gov.in": [
        ("IGOT-SRVY-201", "SURVEY_DESIGN", 2, 3),
    ],
}


async def _seed_prior_training(
    session: AsyncSession,
    user_id: uuid.UUID,
    email: str,
    comps_by_code: dict[str, Competency],
) -> int:
    """Record completed courses and the level they moved.

    Written as a completed enrolment plus two evidence rows, the earlier one
    timestamped before the completion, so the training-effectiveness report has
    a genuine before-and-after to compare rather than a fabricated delta.
    """
    entries = PRIOR_TRAINING.get(email, [])
    if not entries:
        return 0

    written = 0
    for external_id, comp_code, before, after in entries:
        competency = comps_by_code.get(comp_code)
        course = await session.scalar(
            select(Course).where(Course.external_id == external_id)
        )
        if competency is None or course is None:
            continue

        existing = await session.scalar(
            select(Enrollment.id)
            .where(Enrollment.user_id == user_id)
            .where(Enrollment.course_id == course.id)
        )
        if existing is not None:
            continue

        completed_at = datetime.now(tz=timezone.utc) - timedelta(days=90)
        session.add(
            Enrollment(
                user_id=user_id,
                course_id=course.id,
                status="COMPLETED",
                external_ref=f"SEED-{external_id}",
                enrolled_at=completed_at - timedelta(days=30),
                completed_at=completed_at,
            )
        )
        session.add(
            CompetencyEvidence(
                user_id=user_id,
                competency_id=competency.id,
                level=before,
                source_type="self_declared",
                confidence=CONFIDENCE_BY_SOURCE["self_declared"],
                note="Level recorded before the training.",
                created_at=completed_at - timedelta(days=31),
            )
        )
        session.add(
            CompetencyEvidence(
                user_id=user_id,
                competency_id=competency.id,
                level=after,
                source_type="course_completion",
                source_ref=course.id,
                confidence=CONFIDENCE_BY_SOURCE["course_completion"],
                note=f"Completed {course.title}.",
                created_at=completed_at,
            )
        )
        written += 1
    return written


#: Officers whose competency changed *without* attending the programme that
#: targets it. Training effectiveness is only meaningful against a
#: counterfactual: without these rows the comparison group is empty and the
#: net-of-comparison column is honestly blank rather than informative.
#:
#: These are not fabricated attendances. They are ordinary re-declarations and
#: practice attempts, which is how a level moves for someone who did not go on
#: the course.
NON_ATTENDEE_PROGRESSION: dict[str, list[tuple[str, int, int]]] = {
    # email -> [(competency_code, level_before, level_after)]
    "priya.sharma@mospi.gov.in": [("R_STATS", 1, 2)],
    "sunita.devi@mospi.gov.in": [("R_STATS", 1, 1), ("PRICE_STATISTICS", 1, 2)],
    "rakesh.nair@mospi.gov.in": [("PRICE_STATISTICS", 2, 2)],
    "meera.iyer@mospi.gov.in": [("PYTHON", 1, 1)],
    "vikram.rao@mospi.gov.in": [("SURVEY_DESIGN", 1, 2)],
}


async def _seed_non_attendee_progression(
    session: AsyncSession,
    user_id: uuid.UUID,
    email: str,
    comps_by_code: dict[str, Competency],
) -> int:
    """Give the effectiveness report something to compare against."""
    entries = NON_ATTENDEE_PROGRESSION.get(email, [])
    written = 0

    for comp_code, before, after in entries:
        competency = comps_by_code.get(comp_code)
        if competency is None:
            continue

        already = await session.scalar(
            select(func.count())
            .select_from(CompetencyEvidence)
            .where(CompetencyEvidence.user_id == user_id)
            .where(CompetencyEvidence.competency_id == competency.id)
        )
        if (already or 0) >= 2:
            continue

        anchor_at = datetime.now(tz=timezone.utc) - timedelta(days=120)
        session.add(
            CompetencyEvidence(
                user_id=user_id,
                competency_id=competency.id,
                level=before,
                source_type="self_declared",
                confidence=CONFIDENCE_BY_SOURCE["self_declared"],
                note="Earlier self-declaration.",
                created_at=anchor_at,
            )
        )
        session.add(
            CompetencyEvidence(
                user_id=user_id,
                competency_id=competency.id,
                level=after,
                source_type="self_declared",
                confidence=CONFIDENCE_BY_SOURCE["self_declared"],
                note="Re-declared without attending a programme.",
                created_at=anchor_at + timedelta(days=60),
            )
        )
        written += 1
    return written


async def _ensure_auth_user(session: AsyncSession, email: str) -> uuid.UUID:
    """Find or create the local identity for an email."""
    existing = await session.scalar(select(AuthUser).where(AuthUser.email == email))
    if existing is not None:
        return existing.id

    user = AuthUser(
        id=uuid.uuid4(), email=email, encrypted_password=hash_password(DEMO_PASSWORD)
    )
    session.add(user)
    await session.flush()
    return user.id


async def _ensure_baseline(
    session: AsyncSession,
    user_id: uuid.UUID,
    competency_id: uuid.UUID,
    level: int,
) -> bool:
    """Write a self-declared baseline only if nothing is on file yet.

    Never overwrites. If an assessment has since produced a higher level, the
    ledger already holds a newer row and re-seeding must leave it alone.
    """
    already = await session.scalar(
        select(CompetencyEvidence.id)
        .where(CompetencyEvidence.user_id == user_id)
        .where(CompetencyEvidence.competency_id == competency_id)
        .limit(1)
    )
    if already is not None:
        return False

    session.add(
        CompetencyEvidence(
            user_id=user_id,
            competency_id=competency_id,
            level=level,
            source_type="self_declared",
            confidence=CONFIDENCE_BY_SOURCE["self_declared"],
            note="Seeded self-declared baseline.",
        )
    )
    return True


async def seed_users(session: AsyncSession) -> dict[str, int]:
    if settings.AUTH_MODE != "local":
        log.warning(
            "AUTH_MODE=%s: skipping user seed. Identities live in Supabase Auth; "
            "create them with POST /auth/register.",
            settings.AUTH_MODE,
        )
        return {"users": 0, "baselines": 0}

    roles_by_code = {
        r.code: r for r in (await session.execute(select(JobRole))).scalars().all()
    }
    comps_by_code = {
        c.code: c for c in (await session.execute(select(Competency))).scalars().all()
    }
    if not roles_by_code or not comps_by_code:
        raise RuntimeError("Seed the framework before seeding users.")

    user_count = 0
    baseline_count = 0
    trainings = 0
    comparators = 0

    for spec in DEMO_USERS:
        email = str(spec["email"])
        user_id = await _ensure_auth_user(session, email)
        job_role = roles_by_code[str(spec["job_role_code"])]

        await session.execute(
            pg_insert(Profile)
            .values(
                id=user_id,
                full_name=spec["full_name"],
                employee_code=spec["employee_code"],
                designation=spec["designation"],
                station=spec["station"],
                job_role_id=job_role.id,
                cadre=spec["cadre"],
                years_experience=spec["years_experience"],
                education=spec["education"],
            )
            .on_conflict_do_update(
                index_elements=[Profile.id],
                set_={
                    "full_name": spec["full_name"],
                    "designation": spec["designation"],
                    "station": spec["station"],
                    "job_role_id": job_role.id,
                    "cadre": spec["cadre"],
                    "years_experience": spec["years_experience"],
                    "education": spec["education"],
                },
            )
        )

        for role in spec["roles"]:  # type: ignore[union-attr]
            await session.execute(
                pg_insert(UserRole)
                .values(user_id=user_id, role=role)
                .on_conflict_do_nothing(
                    index_elements=[UserRole.user_id, UserRole.role]
                )
            )

        for comp_code, level in dict(spec["baseline"]).items():  # type: ignore[arg-type]
            competency = comps_by_code.get(str(comp_code))
            if competency is None:
                log.warning("baseline references unknown competency %s", comp_code)
                continue
            if await _ensure_baseline(session, user_id, competency.id, int(level)):
                baseline_count += 1

        trainings += await _seed_prior_training(session, user_id, email, comps_by_code)
        comparators += await _seed_non_attendee_progression(
            session, user_id, email, comps_by_code
        )
        user_count += 1

    await session.flush()
    log.info(
        "seeded %d users, %d new self-declared baselines (confidence %s), "
        "%d prior trainings",
        user_count,
        baseline_count,
        CONFIDENCE_BY_SOURCE["self_declared"],
        trainings,
    )
    return {
        "users": user_count,
        "baselines": baseline_count,
        "trainings": trainings,
        "comparators": comparators,
    }


def demo_credentials() -> list[tuple[str, str, str]]:
    """(email, password, description) for the README and the login screen."""
    return [
        (
            str(u["email"]),
            DEMO_PASSWORD,
            f"{u['full_name']} — {u['designation']} ({', '.join(u['roles'])})",  # type: ignore[union-attr]
        )
        for u in DEMO_USERS
    ]


__all__ = ["DEMO_PASSWORD", "DEMO_USERS", "demo_credentials", "seed_users"]
