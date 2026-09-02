"""Seed everything, in dependency order.

    python scripts/seed_all.py                 # framework + users + catalogue
    python scripts/seed_all.py --no-catalogue  # skip the mock service call
    python scripts/seed_all.py --questions     # also seed the fallback question bank

Idempotent throughout. Running it twice in a row is a supported operation and
is part of the acceptance check for this phase.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal, dispose_engine  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.seed.seed_framework import seed_framework  # noqa: E402
from app.seed.seed_users import demo_credentials, seed_users  # noqa: E402

configure_logging()
log = get_logger("seed")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the demo dataset.")
    parser.add_argument(
        "--no-catalogue",
        action="store_true",
        help="skip the catalogue sync (use when the mock service is not running)",
    )
    parser.add_argument(
        "--questions",
        action="store_true",
        help="also seed the fallback SQL question bank",
    )
    parser.add_argument(
        "--corpus",
        action="store_true",
        help="also ingest the sample handout into the assistant's approved corpus",
    )
    args = parser.parse_args()

    print(f"seeding against AUTH_MODE={settings.AUTH_MODE}")

    async with SessionLocal() as session:
        framework = await seed_framework(session)
        print(
            f"  framework    {framework['framework_version']} (sealed) · "
            f"{framework['competencies']} competencies, "
            f"{framework['job_roles']} job roles, "
            f"{framework['activities']} activities, "
            f"{framework['requirements']} requirements, "
            f"{framework['cut_scores']} cut-score sets"
        )

        if not args.no_catalogue:
            from app.services.m6_catalogue.provider import get_catalogue_provider
            from app.services.m6_catalogue.sync import sync_catalogue

            try:
                provider = get_catalogue_provider()
                result = await sync_catalogue(session, provider)
                print(
                    f"  catalogue    {result.upserted} offerings "
                    f"({result.igot} iGOT, {result.nssta} NSSTA), "
                    f"{result.embedded} embedded, provider={result.provider}"
                )
            except Exception as exc:
                print(f"  catalogue    SKIPPED: {exc}")
                print(
                    "               start it with: "
                    "cd mock-catalogue && uvicorn main:app --port 8001"
                )

        users = await seed_users(session)
        print(
            f"  users        {users['users']} users, "
            f"{users['baselines']} new baselines, "
            f"{users.get('trainings', 0)} prior trainings, "
            f"{users.get('comparators', 0)} comparison-group records"
        )

        if args.corpus:
            from app.seed.seed_corpus import seed_corpus

            corpus = await seed_corpus(session)
            print(
                f"  corpus       {corpus['materials']} approved documents, "
                f"{corpus['chunks']} indexed passages"
            )

        if args.questions:
            from app.seed.seed_questions import seed_question_bank

            bank = await seed_question_bank(session)
            print(
                f"  questions    {bank['inserted']} inserted, "
                f"{bank['total']} approved in the bank"
            )

        await session.commit()

    if settings.AUTH_MODE == "local":
        print("\ndemo accounts (local auth):")
        for email, password, description in demo_credentials():
            print(f"  {email:<32} {password:<12} {description}")

    await dispose_engine()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
