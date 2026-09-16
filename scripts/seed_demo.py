"""
NEXORA ATLAS - Demo Seed Script (CLI)
Executes deterministic demo database seeding and prints the health report.
Usage:
    python scripts/seed_demo.py
"""

import sys
import os
import asyncio

# Ensure cross-platform UTF-8 console output for currency and box symbols
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure apps/api is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.core.database import AsyncSessionLocal
from app.demo import seed_demo_data, validate_demo_dataset, format_health_report_text


async def main():
    print("==================================================")
    print("NEXORA ATLAS - Deterministic Demo Dataset Seeder")
    print("==================================================")

    async with AsyncSessionLocal() as session:
        result = await seed_demo_data(session, reset_first=True)
        print(f"Seeding completed successfully: {result['status']}")

        print("\nValidating dataset health...")
        report = await validate_demo_dataset(session)
        print(format_health_report_text(report))


if __name__ == "__main__":
    asyncio.run(main())
