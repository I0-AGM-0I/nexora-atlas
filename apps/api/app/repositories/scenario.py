"""
NEXORA ATLAS - Scenario & ScenarioChange Repository
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.scenario import Scenario, ScenarioChange
from app.repositories.base import BaseRepository


class ScenarioRepository(BaseRepository[Scenario]):
    def __init__(self, session: AsyncSession):
        super().__init__(Scenario, session)

    async def get_with_changes(self, scenario_id: str) -> Optional[Scenario]:
        result = await self.session.execute(
            select(Scenario)
            .options(
                selectinload(Scenario.changes).selectinload(ScenarioChange.resource)
            )
            .where(Scenario.id == scenario_id)
        )
        return result.scalars().first()

    async def list_by_org(self, org_id: str) -> List[Scenario]:
        result = await self.session.execute(
            select(Scenario)
            .options(selectinload(Scenario.changes))
            .where(Scenario.org_id == org_id)
            .order_by(Scenario.created_at.desc())
        )
        return list(result.scalars().all())
