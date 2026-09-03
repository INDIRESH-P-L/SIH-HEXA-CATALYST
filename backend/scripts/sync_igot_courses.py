"""Sync all courses from Mock iGOT Karmayogi (D:\igot) on port 8001 into the local database."""
import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, engine
from app.services.m6_catalogue.mock_provider import MockProvider
from app.services.m6_catalogue.sync import sync_catalogue, mirror_stats

async def main():
    print("Connecting to Mock iGOT Karmayogi at http://localhost:8001...")
    provider = MockProvider()
    
    # Test health
    healthy = await provider.health()
    if not healthy:
        print("[WARNING] Health check to http://localhost:8001 failed or service returned non-200. Proceeding with fetch anyway...")
    else:
        print("[OK] Upstream Mock iGOT service is healthy and reachable.")

    print("Fetching courses from mock iGOT and generating FastEmbed embeddings...")
    async with SessionLocal() as session:
        result = await sync_catalogue(session, provider)
        await session.commit()
        
        stats = await mirror_stats(session)
        print("=" * 60)
        print(f"Sync complete!")
        print(f"  Fetched from mock iGOT: {result.fetched}")
        print(f"  Upserted into database: {result.upserted}")
        print(f"  Embedded vectors:       {result.embedded}")
        print(f"  Total mirror courses:   {stats['total']}")
        print("=" * 60)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
