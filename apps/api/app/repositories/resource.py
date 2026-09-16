"""
NEXORA ATLAS - CloudResource & Tag Repository
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.resource import CloudResource, Tag
from app.repositories.base import BaseRepository


class CloudResourceRepository(BaseRepository[CloudResource]):
    def __init__(self, session: AsyncSession):
        super().__init__(CloudResource, session)

    async def get_by_native_id(self, account_id: str, native_id: str) -> Optional[CloudResource]:
        result = await self.session.execute(
            select(CloudResource)
            .options(selectinload(CloudResource.tags))
            .where(
                CloudResource.account_id == account_id,
                CloudResource.native_id == native_id,
            )
        )
        return result.scalars().first()

    async def get_by_arn(self, resource_arn: str) -> Optional[CloudResource]:
        result = await self.session.execute(
            select(CloudResource)
            .options(selectinload(CloudResource.tags))
            .where(CloudResource.resource_arn == resource_arn)
        )
        return result.scalars().first()

    async def list_by_account(
        self,
        account_id: str,
        service_name: Optional[str] = None,
        resource_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CloudResource]:
        query = (
            select(CloudResource)
            .options(selectinload(CloudResource.tags))
            .where(CloudResource.account_id == account_id)
        )
        if service_name:
            query = query.where(CloudResource.service_name == service_name)
        if resource_type:
            query = query.where(CloudResource.resource_type == resource_type)
        if status:
            query = query.where(CloudResource.status == status)

        query = query.order_by(CloudResource.service_name.asc(), CloudResource.name.asc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class TagRepository(BaseRepository[Tag]):
    def __init__(self, session: AsyncSession):
        super().__init__(Tag, session)

    async def list_by_resource(self, resource_id: str) -> List[Tag]:
        result = await self.session.execute(
            select(Tag).where(Tag.resource_id == resource_id)
        )
        return list(result.scalars().all())
