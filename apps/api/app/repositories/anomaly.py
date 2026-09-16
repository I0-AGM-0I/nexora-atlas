"""
NEXORA ATLAS - Anomaly Repository
"""

from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.anomaly import Anomaly
from app.repositories.base import BaseRepository


class AnomalyRepository(BaseRepository[Anomaly]):
    def __init__(self, session: AsyncSession):
        super().__init__(Anomaly, session)

    async def list_by_account(
        self,
        account_id: str,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Anomaly]:
        query = (
            select(Anomaly)
            .options(selectinload(Anomaly.resource))
            .where(Anomaly.account_id == account_id)
        )
        if severity:
            query = query.where(Anomaly.severity == severity)
        if status:
            query = query.where(Anomaly.status == status)

        query = query.order_by(Anomaly.detected_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_open_count(self, account_id: str) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Anomaly)
            .where(
                Anomaly.account_id == account_id,
                Anomaly.status == "OPEN",
            )
        )
        return result.scalar() or 0
