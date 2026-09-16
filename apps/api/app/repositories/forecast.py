"""
NEXORA ATLAS - Forecast Repository
"""

from typing import List, Optional
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.forecast import Forecast
from app.repositories.base import BaseRepository


class ForecastRepository(BaseRepository[Forecast]):
    def __init__(self, session: AsyncSession):
        super().__init__(Forecast, session)

    async def list_by_account(
        self,
        account_id: str,
        start_month: Optional[date] = None,
        limit: int = 12,
    ) -> List[Forecast]:
        query = select(Forecast).where(Forecast.account_id == account_id)
        if start_month:
            query = query.where(Forecast.forecast_month >= start_month)

        query = query.order_by(Forecast.forecast_month.asc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
