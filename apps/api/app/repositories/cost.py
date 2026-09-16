"""
NEXORA ATLAS - Cost Records & Snapshots Repository
"""

from decimal import Decimal
from typing import Optional, List, Dict
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.cost import CostRecord, CostSnapshot
from app.repositories.base import BaseRepository


class CostRepository(BaseRepository[CostRecord]):
    def __init__(self, session: AsyncSession):
        super().__init__(CostRecord, session)

    async def list_records(
        self,
        account_id: str,
        start_date: date,
        end_date: date,
        service_name: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[CostRecord]:
        query = (
            select(CostRecord)
            .where(
                CostRecord.account_id == account_id,
                CostRecord.usage_date >= start_date,
                CostRecord.usage_date <= end_date,
            )
        )
        if service_name:
            query = query.where(CostRecord.service_name == service_name)

        query = query.order_by(CostRecord.usage_date.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def sum_spend(
        self,
        account_id: str,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        result = await self.session.execute(
            select(func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")))
            .where(
                CostRecord.account_id == account_id,
                CostRecord.usage_date >= start_date,
                CostRecord.usage_date <= end_date,
            )
        )
        return result.scalar() or Decimal("0.0000")

    async def sum_spend_by_service(
        self,
        account_id: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Decimal]:
        result = await self.session.execute(
            select(
                CostRecord.service_name,
                func.sum(CostRecord.unblended_cost).label("total_service_cost"),
            )
            .where(
                CostRecord.account_id == account_id,
                CostRecord.usage_date >= start_date,
                CostRecord.usage_date <= end_date,
            )
            .group_by(CostRecord.service_name)
            .order_by(func.sum(CostRecord.unblended_cost).desc())
        )
        return {row.service_name: row.total_service_cost for row in result}

    async def get_snapshots(
        self,
        account_id: str,
        period_type: str = "MONTHLY",
        limit: int = 12,
    ) -> List[CostSnapshot]:
        result = await self.session.execute(
            select(CostSnapshot)
            .where(
                CostSnapshot.account_id == account_id,
                CostSnapshot.period_type == period_type,
            )
            .order_by(CostSnapshot.period_start.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
