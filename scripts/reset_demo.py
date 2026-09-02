"""Return the database to its opening demonstration state.

    python scripts/reset_demo.py

Clears what a demonstration run produced — assessments and their evidence,
recommendation batches, enrolments, uploaded material and generated questions.
Priya Sharma goes back to SQL level 1, a HIGH gap, which is where the demo
script opens.

Deliberately kept: the competency framework, the users, their self-declared
baselines, the catalogue mirror, the hand-written question bank, the seeded
prior-training history the effectiveness report is built from, and the approved
corpus the assistant answers out of. Those are reference data, not the record
of a demonstration run.
Use ``apply_migrations.py --reset`` for a full teardown instead.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from sqlalchemy import text  # noqa: E402

from app.core.database import SessionLocal, dispose_engine  # noqa: E402
from app.core.logging import configure_logging  # noqa: E402

configure_logging()

# Order matters: children before parents.
# Seeded prior training is reference data, not demonstration activity: it is
# what the problem statement calls "previous trainings", and it is what makes
# the training-effectiveness report non-empty. Clearing it here would leave the
# administrator dashboard looking broken until a full re-seed.
CLEAR_STATEMENTS = [
    ("assessment answers", "delete from assessment_questions"),
    ("assessments", "delete from assessments"),
    ("recommendations", "delete from recommendations"),
    (
        "enrolments made during the demo",
        "delete from enrollments "
        "where external_ref is null or external_ref not like 'SEED-%'",
    ),
    (
        "questions generated during the demo",
        "delete from questions where material_id in ("
        "  select id from learning_materials where storage_path not like 'seed/%'"
        ")",
    ),
    (
        "chunks of uploaded material",
        "delete from material_chunks where material_id in ("
        "  select id from learning_materials where storage_path not like 'seed/%'"
        ")",
    ),
    (
        "materials uploaded during the demo",
        "delete from learning_materials where storage_path not like 'seed/%'",
    ),
    (
        "assessment evidence",
        "delete from competency_evidence where source_type = 'assessment'",
    ),
    ("activity log", "delete from activity_log"),
    ("gap snapshots", "delete from gap_snapshots"),
    ("assistant queries", "delete from assistant_queries"),
    ("outbox entries", "delete from outbox"),
    ("nominations", "delete from nominations"),
    ("events", "delete from events"),
]


async def main() -> int:
    parser = argparse.ArgumentParser(description="Reset the demo state.")
    parser.add_argument(
        "--keep-cache",
        action="store_true",
        help="keep llm_cache, so a pre-warmed offline demo still works",
    )
    parser.add_argument(
        "--keep-question-bank",
        action="store_true",
        default=True,
        help="keep the hand-written SQL bank (default: kept)",
    )
    args = parser.parse_args()

    statements = list(CLEAR_STATEMENTS)
    if not args.keep_cache:
        statements.append(("LLM cache", "delete from llm_cache"))
        statements.append(("LLM audit", "delete from llm_audit"))

    async with SessionLocal() as session:
        for label, statement in statements:
            result = await session.execute(text(statement))
            print(f"  cleared {result.rowcount or 0:>4} {label}")
        await session.commit()

        levels = (
            await session.execute(
                text(
                    "select c.code, uc.current_level "
                    "from user_competency uc "
                    "join competencies c on c.id = uc.competency_id "
                    "join profiles p on p.id = uc.user_id "
                    "where p.full_name = 'Priya Sharma' "
                    "order by c.code"
                )
            )
        ).all()

    await dispose_engine()

    if levels:
        print("\nPriya Sharma is back to her seeded baseline:")
        for code, level in levels:
            print(f"  {code:<18} level {level}")
    print(
        "\nRe-run the seed if the framework or catalogue also need refreshing:"
        "\n  python scripts/seed_all.py --questions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
