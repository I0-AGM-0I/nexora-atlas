"""
NEXORA ATLAS - Optimization Opportunity & Recommendation Repository
"""

from decimal import Decimal
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.optimization import OptimizationOpportunity, Recommendation
from app.repositories.base import BaseRepository


class OptimizationOpportunityRepository(BaseRepository[OptimizationOpportunity]):
    def __init__(self, session: AsyncSession):
        super().__init__(OptimizationOpportunity, session)

    async def list_by_account(
        self,
        account_id: str,
        category: Optional[str] = None,
        status: Optional[str] = "OPEN",
    ) -> List[OptimizationOpportunity]:
        query = (
            select(OptimizationOpportunity)
            .options(
                selectinload(OptimizationOpportunity.recommendations),
                selectinload(OptimizationOpportunity.resource),
            )
            .where(OptimizationOpportunity.account_id == account_id)
        )
        if category:
            query = query.where(OptimizationOpportunity.category == category)
        if status:
            query = query.where(OptimizationOpportunity.status == status)

        result = await self.session.execute(query.order_by(OptimizationOpportunity.estimated_waste_monthly.desc()))
        return list(result.scalars().all())


class RecommendationRepository(BaseRepository[Recommendation]):
    def __init__(self, session: AsyncSession):
        super().__init__(Recommendation, session)

    async def get_with_evidence(self, recommendation_id: str) -> Optional[Recommendation]:
        result = await self.session.execute(
            select(Recommendation)
            .options(
                selectinload(Recommendation.resource),
                selectinload(Recommendation.opportunity),
            )
            .where(Recommendation.id == recommendation_id)
        )
        return result.scalars().first()

    async def list_active(
        self,
        category: Optional[str] = None,
        risk_level: Optional[str] = None,
        status: str = "OPEN",
        limit: int = 50,
        offset: int = 0,
    ) -> List[Recommendation]:
        query = (
            select(Recommendation)
            .options(selectinload(Recommendation.resource))
            .where(Recommendation.status == status)
        )
        if category:
            query = query.where(Recommendation.category == category)
        if risk_level:
            query = query.where(Recommendation.risk_level == risk_level)

        query = query.order_by(Recommendation.estimated_monthly_savings.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def sum_potential_savings(self, status: str = "OPEN") -> Decimal:
        result = await self.session.execute(
            select(func.coalesce(func.sum(Recommendation.estimated_monthly_savings), Decimal("0.0000")))
            .where(Recommendation.status == status)
        )
        return result.scalar() or Decimal("0.0000")
