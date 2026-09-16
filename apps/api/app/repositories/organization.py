"""
NEXORA ATLAS - Organization Repository
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organization import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, session: AsyncSession):
        super().__init__(Organization, session)

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        result = await self.session.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalars().first()

    async def list_active(self) -> List[Organization]:
        result = await self.session.execute(
            select(Organization).order_by(Organization.name.asc())
        )
        return list(result.scalars().all())
