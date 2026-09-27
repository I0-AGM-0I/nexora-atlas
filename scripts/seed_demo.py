"""
NEXORA ATLAS - Demo Seed Script (CLI)
Executes deterministic demo database seeding and prints the health report.
Usage:
    python scripts/seed_demo.py          # Non-destructive startup (seeds only if missing)
    python scripts/seed_demo.py --reset  # Explicitly reset & re-seed demo data
"""

import sys
import os
import asyncio
import argparse

# Ensure cross-platform UTF-8 console output for currency and box symbols
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure apps/api is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.core.database import AsyncSessionLocal, engine
from app.models import Base
from app.demo import seed_demo_data, validate_demo_dataset, format_health_report_text


async def main():
    parser = argparse.ArgumentParser(description="NEXORA ATLAS Demo Dataset Seeder")
    parser.add_argument(
        "--reset",
        action="store_true",
        default=False,
        help="Force wipe and re-seed demo dataset (destructive reset)",
    )
    args = parser.parse_args()

    print("==================================================")
    print("NEXORA ATLAS - Deterministic Demo Dataset Seeder")
    print("==================================================")

    # Ensure all tables exist (non-destructive DDL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await seed_demo_data(session, reset_first=args.reset)
        if result.get("status") == "already_seeded":
            print(f"Demo dataset already initialized for '{result.get('organization')}'. Existing data preserved.")
        else:
            print(f"Seeding completed successfully: {result.get('status')}")
            print("\nValidating dataset health...")
            try:
                report = await validate_demo_dataset(session)
                print(format_health_report_text(report))
            except AssertionError as e:
                print(f"Validation note: {e}")


if __name__ == "__main__":
    asyncio.run(main())
