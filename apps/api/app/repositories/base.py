"""
NEXORA ATLAS - Generic Base Repository
Isolates database access operations from services and route handlers.
"""

from typing import Generic, TypeVar, Type, Optional, List, Sequence
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, entity_id: str) -> Optional[ModelType]:
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        return result.scalars().first()

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(self.model))
        return result.scalar() or 0

    async def create(self, entity: ModelType) -> ModelType:
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def bulk_create(self, entities: Sequence[ModelType]) -> Sequence[ModelType]:
        self.session.add_all(entities)
        await self.session.commit()
        return entities

    async def update(self, entity: ModelType) -> ModelType:
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete_by_id(self, entity_id: str) -> bool:
        result = await self.session.execute(
            delete(self.model).where(self.model.id == entity_id)
        )
        await self.session.commit()
        return (result.rowcount or 0) > 0
