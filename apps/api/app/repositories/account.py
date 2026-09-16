"""
NEXORA ATLAS - CloudAccount & Region Repository
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.account import CloudAccount, CloudRegion
from app.repositories.base import BaseRepository


class CloudAccountRepository(BaseRepository[CloudAccount]):
    def __init__(self, session: AsyncSession):
        super().__init__(CloudAccount, session)

    async def get_by_account_id(self, org_id: str, account_id: str, provider_type: str = "AWS") -> Optional[CloudAccount]:
        result = await self.session.execute(
            select(CloudAccount).where(
                CloudAccount.org_id == org_id,
                CloudAccount.account_id == account_id,
                CloudAccount.provider_type == provider_type,
            )
        )
        return result.scalars().first()

    async def list_by_org(self, org_id: str) -> List[CloudAccount]:
        result = await self.session.execute(
            select(CloudAccount).where(CloudAccount.org_id == org_id).order_by(CloudAccount.name.asc())
        )
        return list(result.scalars().all())


class CloudRegionRepository(BaseRepository[CloudRegion]):
    def __init__(self, session: AsyncSession):
        super().__init__(CloudRegion, session)

    async def get_by_code(self, region_code: str, provider_type: str = "AWS") -> Optional[CloudRegion]:
        result = await self.session.execute(
            select(CloudRegion).where(
                CloudRegion.region_code == region_code,
                CloudRegion.provider_type == provider_type,
            )
        )
        return result.scalars().first()
