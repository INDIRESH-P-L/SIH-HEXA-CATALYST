"""Pre-warm the LLM response cache.

Two jobs:

  * The demonstration has to survive a dead network or an exhausted free-tier
    quota. Every cached response is served without a call.
  * A cold first call to a 70B model costs several seconds. Pre-warming means
    the interface responds immediately when it matters.

Run it once with a working GROQ_API_KEY and the responses are stored against
the same sha256(prompt-version + model + purpose + system + prompt) key the
runtime computes, so a later request with the same inputs hits the cache. Run
it with no key and it reports what it would have warmed, and warms nothing —
it never fabricates a model response.

    python -m app.seed.seed_demo_cache            # from backend/
    python -m app.seed.seed_demo_cache --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sqlalchemy import func, select  # noqa: E402

from app.ai import prompts  # noqa: E402
from app.ai.llm_client import complete  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal, dispose_engine  # noqa: E402
from app.core.errors import AppError  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.models.ai import LLMCache  # noqa: E402
from app.models.competency import Competency  # noqa: E402
from app.models.user import JobRole, Profile  # noqa: E402
from app.services import m2_framework as framework  # noqa: E402
from app.services import m4_gap_engine as engine  # noqa: E402
from app.services import m5_recommender as recommender  # noqa: E402

configure_logging()
log = get_logger("seed_demo_cache")

DEMO_EMAIL = "priya.sharma@mospi.gov.in"


async def warm_recommendations(session, profile: Profile, dry_run: bool) -> int:
    """Warm one explanation for every course the demo officer could be shown.

    Runs the real retrieval and ranking, then asks for the explanation of each
    ranked candidate — so the cached keys are exactly the ones the live request
    will compute.
    """
    requirements = await framework.load_requirement_specs(session, profile.job_role_id)
    levels = await framework.load_current_levels(session, profile.id)
    gap_rows = engine.build_gap_rows(requirements, levels)
    targets = engine.target_gaps(gap_rows, limit=recommender.MAX_TARGET_GAPS)
    if not targets:
        log.warning("demo officer has no open gaps; nothing to warm")
        return 0

    candidates = await recommender.retrieve_candidates(session, targets)
    job_role = await framework.resolve_job_role_for_user(session, profile)
    title = job_role.title if job_role else "Statistical Officer"

    warmed = 0
    for candidate in candidates.values():
        context = recommender.build_ai_context(profile, title, candidate)
        if dry_run:
            warmed += 1
            continue
        _text, source, _model = await recommender.explain(
            session, context=context, user_id=profile.id
        )
        if source == "ai":
            warmed += 1
    return warmed


async def warm_feedback(session, profile: Profile, dry_run: bool) -> int:
    """Warm quiz feedback across the score range the demo might produce."""
    from app.ai import scrub

    competency = await session.scalar(select(Competency).where(Competency.code == "SQL"))
    if competency is None:
        return 0

    # The scripted run lands on 85%; the neighbours cover a mistyped answer.
    scenarios = [
        (85.0, 17, 20, ["JOIN types", "GROUP BY with HAVING"]),
        (90.0, 18, 20, ["JOIN types"]),
        (80.0, 16, 20, ["JOIN types", "Null handling"]),
        (90.0, 9, 10, ["JOIN types"]),
        (100.0, 20, 20, []),
    ]

    warmed = 0
    for score, correct, total, weak in scenarios:
        context = scrub.build_context(
            competency_name=competency.name,
            score=score,
            correct_count=correct,
            total_questions=total,
            weak_topics=", ".join(weak) if weak else "none",
            strong_topics="SELECT and filtering, Aggregate functions",
        )
        if dry_run:
            warmed += 1
            continue
        try:
            await complete(
                session=session,
                purpose="feedback",
                prompt=prompts.FEEDBACK.format(**context),
                system=prompts.SYSTEM_FEEDBACK,
                user_id=profile.id,
                temperature=0.4,
                max_tokens=220,
            )
            warmed += 1
        except AppError as exc:
            log.info("feedback warm skipped: %s", exc.message)
    return warmed


async def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-warm the LLM cache.")
    parser.add_argument(
        "--dry-run", action="store_true", help="report what would be warmed"
    )
    args = parser.parse_args()

    if not settings.llm_configured and not args.dry_run:
        print(
            "No GROQ_API_KEY is configured, so there is nothing to warm.\n"
            "The application already works without it: every AI feature falls\n"
            "back to a deterministic template. Set GROQ_API_KEY in backend/.env\n"
            "and re-run this to make the demonstration show model-written text\n"
            "with the network disconnected."
        )
        return 0

    async with SessionLocal() as session:
        profile = await session.scalar(
            select(Profile)
            .join(JobRole, JobRole.id == Profile.job_role_id)
            .where(Profile.full_name == "Priya Sharma")
        )
        if profile is None:
            print("Demo officer not found. Run scripts/seed_all.py first.")
            return 1

        before = await session.scalar(select(func.count()).select_from(LLMCache)) or 0

        explanations = await warm_recommendations(session, profile, args.dry_run)
        feedback = await warm_feedback(session, profile, args.dry_run)

        if not args.dry_run:
            await session.commit()

        after = await session.scalar(select(func.count()).select_from(LLMCache)) or 0

    await dispose_engine()

    verb = "would warm" if args.dry_run else "warmed"
    print(f"  {verb} {explanations} recommendation explanations")
    print(f"  {verb} {feedback} feedback responses")
    if not args.dry_run:
        print(f"  llm_cache rows: {before} -> {after}")
        print(
            "\nThe demonstration will now serve these from cache, with no network "
            "call and no token spend."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
