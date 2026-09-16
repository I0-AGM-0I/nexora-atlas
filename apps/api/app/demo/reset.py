"""
NEXORA ATLAS - Safe Scoped Demo Reset
Wipes exclusively demo records (is_demo=True) while preserving real production data.
"""

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organization import Organization, AuditLog
from app.models.account import CloudRegion
from app.demo.config import DEMO_ORG_SLUG
from app.core.logging import logger


from typing import Dict, Any

async def reset_demo_data(session: AsyncSession) -> Dict[str, Any]:
    """
    Safely purges only organizations marked with is_demo=True.
    Cascading foreign keys clean all related child records.
    """
    logger.info("Executing safe scoped demo dataset reset...")

    # Find demo organizations
    result = await session.execute(
        select(Organization).where(Organization.is_demo.is_(True))
    )
    demo_orgs = list(result.scalars().all())

    deleted_count = len(demo_orgs)
    for org in demo_orgs:
        await session.delete(org)

    await session.commit()
    logger.info(f"Demo reset complete. Purged {deleted_count} demo organization(s).")

    return {
        "status": "reset_complete",
        "demo_organizations_purged": deleted_count,
    }
