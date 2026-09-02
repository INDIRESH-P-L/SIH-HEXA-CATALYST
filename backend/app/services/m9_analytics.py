"""M9 · Analytics & Competency Tracking.

Observation layer. An event backbone, two dashboards, and the one metric that
says whether training worked.

Every figure here is a count, a mean or a difference over rows that exist.
Nothing is predicted, modelled or inferred, and the response payloads say so.

Two rules that shape everything below:

  * **k-anonymity.** No aggregate is shown over fewer than five officers, and
    no individual score appears in any MDO-wide view. A suppressed cell says
    it was suppressed rather than reading as zero.
  * **Practice attempts stay out of administrator dashboards.** They are real
    evidence for the learner at 0.50 confidence, and noise for workforce
    planning.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture import (
    FrameworkVersion,
    MartCompetency,
    MartTrainingEffectiveness,
)
from app.models.assessment import Assessment
from app.models.competency import Competency
from app.models.course import Course, Enrollment
from app.models.evidence import CompetencyEvidence, UserCompetency
from app.models.user import JobRole, Profile
from app.schemas.analytics import (
    AdminOverview,
    CompetencyGapFrequency,
    CompetencyMatrix,
    LevelDistributionBucket,
    MatrixCell,
    MyAnalytics,
    ProgressPoint,
    RadarPoint,
    StatTile,
    TrainingEffectiveness,
    TrainingEffectivenessRow,
)
from app.services import m2_framework as framework
from app.services import m4_gap_engine as engine
from app.services import m9_events as events

#: The radar reads badly past eight axes.
MAX_RADAR_AXES = 8

#: Points kept on the progress line.
MAX_PROGRESS_POINTS = 40

#: No aggregate is published over fewer officers than this.
K_ANONYMITY_THRESHOLD = 5


def suppressed(count: int) -> bool:
    """Whether a cell must be withheld to protect individuals."""
    return 0 < count < K_ANONYMITY_THRESHOLD


# ── learner dashboard ────────────────────────────────────────────────────────


async def my_analytics(session: AsyncSession, profile: Profile) -> MyAnalytics:
    requirements = (
        await framework.load_requirement_specs(session, profile.job_role_id)
        if profile.job_role_id
        else []
    )
    observations = await framework.load_observations(session, profile.id)
    rows = engine.build_gap_rows(requirements, observations)
    summary = engine.summarise(rows)

    radar = [
        RadarPoint(
            competency_code=r.competency_code,
            competency_name=r.competency_name,
            current_level=r.current_level,
            required_level=r.required_level,
        )
        for r in sorted(rows, key=lambda x: (x.cluster, x.competency_name))[:MAX_RADAR_AXES]
    ]

    # Progress: one point per evidence event, stamped with the moment that
    # evidence was written. Bucketing by calendar day would collapse a whole
    # session into a single point.
    evidence = (
        await session.execute(
            select(
                CompetencyEvidence.created_at,
                CompetencyEvidence.competency_id,
                CompetencyEvidence.level,
            )
            .where(CompetencyEvidence.user_id == profile.id)
            .order_by(CompetencyEvidence.created_at)
        )
    ).all()

    codes = {
        str(c.id): c.code
        for c in (await session.execute(select(Competency))).scalars().all()
    }
    running: dict[str, int] = {}
    progress: list[ProgressPoint] = []
    for created_at, competency_id, level in evidence:
        running[str(competency_id)] = int(level)
        progress.append(
            ProgressPoint(
                at=created_at,
                average_level=round(sum(running.values()) / len(running), 2),
                competency_code=codes.get(str(competency_id)),
                level=int(level),
            )
        )
    progress = progress[-MAX_PROGRESS_POINTS:]

    hours = await session.scalar(
        select(func.coalesce(func.sum(Course.duration_hours), 0))
        .select_from(Enrollment)
        .join(Course, Course.id == Enrollment.course_id)
        .where(Enrollment.user_id == profile.id)
        .where(Enrollment.status == "COMPLETED")
    )
    completed = await session.scalar(
        select(func.count())
        .select_from(Enrollment)
        .where(Enrollment.user_id == profile.id)
        .where(Enrollment.status == "COMPLETED")
    )
    in_progress = await session.scalar(
        select(func.count())
        .select_from(Enrollment)
        .where(Enrollment.user_id == profile.id)
        .where(Enrollment.status.in_(("ENROLLED", "IN_PROGRESS", "NOMINATION_REQUESTED")))
    )
    assessments_taken = await session.scalar(
        select(func.count())
        .select_from(Assessment)
        .where(Assessment.user_id == profile.id)
        .where(Assessment.status == "SUBMITTED")
    )
    levels_gained = await session.scalar(
        select(func.coalesce(func.sum(Assessment.level_after - Assessment.level_before), 0))
        .where(Assessment.user_id == profile.id)
        .where(Assessment.status == "SUBMITTED")
    )

    return MyAnalytics(
        competencies_tracked=summary.total_competencies,
        average_current_level=summary.average_current_level,
        average_required_level=summary.average_required_level,
        gaps_open=summary.open_gaps,
        critical_gaps=summary.critical,
        stale_competencies=summary.stale_count,
        unassessed_competencies=summary.unassessed_count,
        learning_hours_completed=int(hours or 0),
        courses_completed=int(completed or 0),
        courses_in_progress=int(in_progress or 0),
        assessments_taken=int(assessments_taken or 0),
        levels_gained=int(levels_gained or 0),
        radar=radar,
        progress=progress,
        tiles=[
            StatTile(label="Competencies tracked", value=summary.total_competencies),
            StatTile(label="Open gaps", value=summary.open_gaps),
            StatTile(label="Critical", value=summary.critical),
            StatTile(label="Needs re-assessment", value=summary.stale_count + summary.unassessed_count),
            StatTile(label="Learning hours", value=int(hours or 0), unit="h"),
        ],
    )


# ── workforce aggregates ─────────────────────────────────────────────────────


async def _all_gap_rows(
    session: AsyncSession,
) -> list[tuple[uuid.UUID, str, engine.GapRow]]:
    """Gap rows for every officer who has a job role."""
    profiles = (
        await session.execute(
            select(Profile, JobRole).join(JobRole, JobRole.id == Profile.job_role_id)
        )
    ).all()

    cache: dict[uuid.UUID, list[engine.Requirement]] = {}
    out: list[tuple[uuid.UUID, str, engine.GapRow]] = []
    now = datetime.now(tz=timezone.utc)

    for profile, job_role in profiles:
        if job_role.id not in cache:
            cache[job_role.id] = await framework.load_requirement_specs(session, job_role.id)
        observations = await framework.load_observations(session, profile.id)
        for row in engine.build_gap_rows(cache[job_role.id], observations, now=now):
            out.append((profile.id, job_role.code, row))
    return out


async def admin_overview(session: AsyncSession) -> AdminOverview:
    total_officers = await session.scalar(select(func.count()).select_from(Profile))
    total_competencies = await session.scalar(select(func.count()).select_from(Competency))
    total_courses = await session.scalar(select(func.count()).select_from(Course))
    # Practice attempts do not count towards workforce measurement.
    total_assessments = await session.scalar(
        select(func.count())
        .select_from(Assessment)
        .where(Assessment.status == "SUBMITTED")
        .where(Assessment.mode == "proctored")
    )

    rows = await _all_gap_rows(session)

    band_counts: dict[str, int] = {band.value: 0 for band in engine.GapBand}
    per_competency: dict[str, list[engine.GapRow]] = defaultdict(list)
    officers_with_critical: set[uuid.UUID] = set()

    for user_id, _role_code, row in rows:
        band_counts[row.band.value] += 1
        per_competency[row.competency_code].append(row)
        if row.band is engine.GapBand.CRITICAL:
            officers_with_critical.add(user_id)

    gap_frequency: list[CompetencyGapFrequency] = []
    for code, entries in per_competency.items():
        officers = len({e.competency_id for e in entries}) and len(entries)
        with_gap = [e for e in entries if e.gap > 0]
        bands = [e.band.value for e in entries]
        dominant = max(set(bands), key=bands.count)
        is_suppressed = suppressed(len(entries))
        gap_frequency.append(
            CompetencyGapFrequency(
                competency_code=code,
                competency_name=entries[0].competency_name,
                officers_with_gap=0 if is_suppressed else len(with_gap),
                average_gap=0.0 if is_suppressed else round(sum(e.gap for e in entries) / officers, 2),
                average_current_level=(
                    0.0 if is_suppressed else round(sum(e.current_level for e in entries) / officers, 2)
                ),
                average_required_level=(
                    0.0 if is_suppressed else round(sum(e.required_level for e in entries) / officers, 2)
                ),
                dominant_band=dominant,  # type: ignore[arg-type]
                officers=len(entries),
                suppressed=is_suppressed,
            )
        )
    gap_frequency.sort(key=lambda g: (-g.officers_with_gap, -g.average_gap))

    distribution = (
        await session.execute(
            select(UserCompetency.current_level, func.count())
            .group_by(UserCompetency.current_level)
            .order_by(UserCompetency.current_level)
        )
    ).all()

    stale = sum(1 for _u, _r, row in rows if row.stale)
    unassessed = sum(1 for _u, _r, row in rows if not row.source_type)
    stream = await events.stream_size(session)

    return AdminOverview(
        total_officers=int(total_officers or 0),
        total_competencies=int(total_competencies or 0),
        total_courses=int(total_courses or 0),
        total_assessments=int(total_assessments or 0),
        officers_with_critical_gap=len(officers_with_critical),
        stale_evidence_rows=stale,
        unassessed_requirements=unassessed,
        events_recorded=stream,
        band_counts=band_counts,
        level_distribution=[
            LevelDistributionBucket(
                level=int(level), frac_label=engine.frac_label(int(level)), count=int(count)
            )
            for level, count in distribution
        ],
        gap_frequency=gap_frequency,
        tiles=[
            StatTile(label="Officers", value=int(total_officers or 0)),
            StatTile(label="Competencies", value=int(total_competencies or 0)),
            StatTile(label="Catalogue offerings", value=int(total_courses or 0)),
            StatTile(label="Proctored assessments", value=int(total_assessments or 0)),
            StatTile(label="Critical-gap officers", value=len(officers_with_critical)),
        ],
    )


async def competency_matrix(session: AsyncSession) -> CompetencyMatrix:
    """Role × competency average level, for the workforce heatmap."""
    rows = await _all_gap_rows(session)

    grouped: dict[tuple[str, str], list[engine.GapRow]] = defaultdict(list)
    for _user_id, role_code, row in rows:
        grouped[(role_code, row.competency_code)].append(row)

    titles = dict((await session.execute(select(JobRole.code, JobRole.title))).all())

    cells = []
    for (role_code, competency_code), entries in grouped.items():
        is_suppressed = suppressed(len(entries))
        cells.append(
            MatrixCell(
                job_role_code=role_code,
                job_role_title=titles.get(role_code, role_code),
                competency_code=competency_code,
                competency_name=entries[0].competency_name,
                average_level=(
                    0.0
                    if is_suppressed
                    else round(sum(e.current_level for e in entries) / len(entries), 2)
                ),
                required_level=entries[0].required_level,
                officers=len(entries),
                suppressed=is_suppressed,
            )
        )
    cells.sort(key=lambda c: (c.job_role_title, c.competency_code))

    return CompetencyMatrix(
        job_roles=sorted({c.job_role_title for c in cells}),
        competencies=sorted({c.competency_code for c in cells}),
        cells=cells,
        k_anonymity_threshold=K_ANONYMITY_THRESHOLD,
    )


# ── the metric nobody else shows ─────────────────────────────────────────────


async def training_effectiveness(session: AsyncSession) -> TrainingEffectiveness:
    """Pre/post competency delta per programme, against a comparison group.

    Completion percentage answers "did they attend". This answers "did it
    work" — and it is the number a capacity-building unit needs in order to
    decide which programmes are worth the seats.

    The comparison group is officers who did *not* attend, measured over the
    same competency in the same period. It is not a randomised control and the
    payload says so; it is the honest available counterfactual.
    """
    completions = (
        await session.execute(
            select(Enrollment, Course, Competency)
            .join(Course, Course.id == Enrollment.course_id)
            .join(Competency, Competency.code == Course.competency_code)
            .where(Enrollment.status == "COMPLETED")
            .where(Enrollment.completed_at.isnot(None))
        )
    ).all()

    grouped: dict[uuid.UUID, list[tuple[int, int]]] = defaultdict(list)
    course_meta: dict[uuid.UUID, Course] = {}
    attendees_by_competency: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)

    for enrollment, course, competency in completions:
        course_meta[course.id] = course
        attendees_by_competency[competency.id].add(enrollment.user_id)

        before = await session.scalar(
            select(CompetencyEvidence.level)
            .where(CompetencyEvidence.user_id == enrollment.user_id)
            .where(CompetencyEvidence.competency_id == competency.id)
            .where(CompetencyEvidence.created_at <= enrollment.completed_at)
            .order_by(CompetencyEvidence.created_at.desc())
            .limit(1)
        )
        after = await session.scalar(
            select(CompetencyEvidence.level)
            .where(CompetencyEvidence.user_id == enrollment.user_id)
            .where(CompetencyEvidence.competency_id == competency.id)
            .order_by(CompetencyEvidence.created_at.desc())
            .limit(1)
        )
        if before is None or after is None:
            continue
        grouped[course.id].append((int(before), int(after)))

    rows: list[TrainingEffectivenessRow] = []
    for course_id, pairs in grouped.items():
        course = course_meta[course_id]
        befores = [b for b, _a in pairs]
        afters = [a for _b, a in pairs]
        delta = round((sum(afters) - sum(befores)) / len(pairs), 2)

        comparison = await _comparison_delta(
            session, course.competency_code, attendees_by_competency
        )

        rows.append(
            TrainingEffectivenessRow(
                course_id=course_id,
                course_title=course.title,
                source=course.source,
                competency_code=course.competency_code,
                completions=len(pairs),
                average_level_before=round(sum(befores) / len(befores), 2),
                average_level_after=round(sum(afters) / len(afters), 2),
                average_delta=delta,
                comparison_delta=comparison,
                net_delta=(round(delta - comparison, 2) if comparison is not None else None),
                suppressed=suppressed(len(pairs)),
            )
        )
    rows.sort(key=lambda r: -r.average_delta)
    return TrainingEffectiveness(rows=rows, k_anonymity_threshold=K_ANONYMITY_THRESHOLD)


async def _comparison_delta(
    session: AsyncSession,
    competency_code: str,
    attendees_by_competency: dict[uuid.UUID, set[uuid.UUID]],
) -> float | None:
    """Average level change over the same competency among non-attendees."""
    competency = await session.scalar(
        select(Competency).where(Competency.code == competency_code)
    )
    if competency is None:
        return None
    attendees = attendees_by_competency.get(competency.id, set())

    rows = (
        await session.execute(
            select(
                CompetencyEvidence.user_id,
                func.min(CompetencyEvidence.level),
                func.max(CompetencyEvidence.level),
                func.count(),
            )
            .where(CompetencyEvidence.competency_id == competency.id)
            .group_by(CompetencyEvidence.user_id)
            .having(func.count() > 1)
        )
    ).all()

    deltas = [
        int(highest) - int(lowest)
        for user_id, lowest, highest, _n in rows
        if user_id not in attendees
    ]
    if not deltas:
        return None
    return round(sum(deltas) / len(deltas), 2)


# ── rollup jobs ──────────────────────────────────────────────────────────────


async def rebuild_marts(session: AsyncSession) -> dict[str, int]:
    """Rebuild the marts from current state.

    In production this runs nightly off the event stream. Here it is exposed
    as an administrator action so the pipeline can be demonstrated rather than
    described.
    """
    version = await framework.current_framework_version(session)

    await session.execute(MartCompetency.__table__.delete())
    await session.execute(MartTrainingEffectiveness.__table__.delete())

    rows = await _all_gap_rows(session)
    role_ids = dict(
        (await session.execute(select(JobRole.code, JobRole.id))).all()
    )
    competency_ids = dict(
        (await session.execute(select(Competency.code, Competency.id))).all()
    )

    grouped: dict[tuple[str, str], list[engine.GapRow]] = defaultdict(list)
    for _user_id, role_code, row in rows:
        grouped[(role_code, row.competency_code)].append(row)

    competency_rows = 0
    for (role_code, competency_code), entries in grouped.items():
        session.add(
            MartCompetency(
                job_role_id=role_ids.get(role_code),
                competency_id=competency_ids.get(competency_code),
                framework_version_id=version.id if version else None,
                officers=len(entries),
                avg_current_level=round(sum(e.current_level for e in entries) / len(entries), 2),
                avg_required_level=round(sum(e.required_level for e in entries) / len(entries), 2),
                officers_with_gap=sum(1 for e in entries if e.gap > 0),
            )
        )
        competency_rows += 1

    effectiveness = await training_effectiveness(session)
    for row in effectiveness.rows:
        session.add(
            MartTrainingEffectiveness(
                course_id=row.course_id,
                cohort=version.version if version else None,
                attendees=row.completions,
                avg_level_before=row.average_level_before,
                avg_level_after=row.average_level_after,
                avg_delta=row.average_delta,
                comparison_delta=row.comparison_delta,
            )
        )

    await session.flush()
    return {
        "competency_rows": competency_rows,
        "effectiveness_rows": len(effectiveness.rows),
        "events_in_stream": await events.stream_size(session),
    }
