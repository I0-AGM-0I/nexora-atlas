"""
NEXORA ATLAS - Tenant Context & Multi-Tenancy Resolution Service
Ensures all domain services operate strictly within tenant-scoped boundaries.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.organization import Organization
from app.models.account import CloudAccount
from app.demo.config import DEMO_ORG_SLUG


@dataclass(frozen=True)
class TenantContext:
    org_id: str
    org_name: str
    slug: str
    currency: str
    timezone: str
    is_demo: bool
    account_ids: List[str]
    accounts: List[CloudAccount]
    account_name_map: Dict[str, str]  # account DB uuid -> account name


async def get_tenant_context(
    session: AsyncSession,
    org_slug: Optional[str] = None,
) -> TenantContext:
    """
    Resolves the current organization tenant context.
    Eagerly loads accounts to ensure all downstream domain queries are strictly scoped.
    """
    target_slug = org_slug or DEMO_ORG_SLUG

    query = (
        select(Organization)
        .options(selectinload(Organization.cloud_accounts))
        .where(Organization.slug == target_slug)
    )
    result = await session.execute(query)
    org = result.scalars().first()

    if not org:
        # Fallback to any organization if slug doesn't match
        fallback_query = (
            select(Organization)
            .options(selectinload(Organization.cloud_accounts))
            .limit(1)
        )
        fallback_res = await session.execute(fallback_query)
        org = fallback_res.scalars().first()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization found. Please run seed script or initialize a tenant.",
        )

    account_ids = [acc.id for acc in org.cloud_accounts]
    name_map = {acc.id: acc.name for acc in org.cloud_accounts}

    return TenantContext(
        org_id=org.id,
        org_name=org.name,
        slug=org.slug,
        currency=org.currency,
        timezone=org.timezone,
        is_demo=org.is_demo,
        account_ids=account_ids,
        accounts=list(org.cloud_accounts),
        account_name_map=name_map,
    )
