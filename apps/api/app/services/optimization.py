"""
NEXORA ATLAS - Optimization Service
Maintains clear structural hierarchy: Opportunity (Problem/Waste) -> Recommendations (Actionable Options).
"""

from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.optimization import OptimizationOpportunity, Recommendation
from app.services.tenant import TenantContext
from app.schemas.optimization import (
    OpportunityItem,
    RecommendationItem,
    OptimizationOverviewResponse,
)


class OptimizationService:
    @classmethod
    def _to_schema(cls, opp: OptimizationOpportunity, account_name_map: dict) -> OpportunityItem:
        recs = [
            RecommendationItem(
                id=r.id,
                opportunity_id=r.opportunity_id,
                title=r.title,
                category=r.category,
                current_configuration=r.current_configuration,
                recommended_configuration=r.recommended_configuration,
                estimated_monthly_savings=r.estimated_monthly_savings,
                estimated_annual_savings=r.estimated_annual_savings,
                confidence_pct=r.confidence_pct,
                risk_level=r.risk_level,
                reasoning=r.reasoning,
            )
            for r in opp.recommendations
        ]
        return OpportunityItem(
            id=opp.id,
            account_id=opp.account_id,
            account_name=account_name_map.get(opp.account_id, "Unknown"),
            resource_id=opp.resource_id,
            resource_name=opp.resource.name if opp.resource else None,
            resource_native_id=opp.resource.native_id if opp.resource else None,
            category=opp.category,
            waste_type=opp.waste_type,
            severity=opp.severity,
            status=opp.status,
            estimated_waste_monthly=opp.estimated_waste_monthly,
            estimated_waste_annual=opp.estimated_waste_monthly * Decimal("12.0000"),
            evidence_json=opp.evidence_json,
            recommendations=recs,
        )

    @classmethod
    async def get_overview(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status_filter: Optional[str] = "OPEN",
    ) -> OptimizationOverviewResponse:
        """Retrieves optimization opportunities and aggregated potential savings."""
        query = (
            select(OptimizationOpportunity)
            .options(
                selectinload(OptimizationOpportunity.resource),
                selectinload(OptimizationOpportunity.recommendations),
            )
            .where(OptimizationOpportunity.account_id.in_(tenant.account_ids))
        )
        if category:
            query = query.where(OptimizationOpportunity.category == category.upper())
        if severity:
            query = query.where(OptimizationOpportunity.severity == severity.upper())
        if status_filter:
            query = query.where(OptimizationOpportunity.status == status_filter.upper())

        query = query.order_by(OptimizationOpportunity.estimated_waste_monthly.desc())
        result = await session.execute(query)
        opps = list(result.scalars().all())

        # Total savings calculation
        savings_res = await session.execute(
            select(func.coalesce(func.sum(OptimizationOpportunity.estimated_waste_monthly), Decimal("0.0000")))
            .where(
                OptimizationOpportunity.account_id.in_(tenant.account_ids),
                OptimizationOpportunity.status == "OPEN",
            )
        )
        potential_monthly_savings = savings_res.scalar() or Decimal("0.0000")
        potential_annual_savings = potential_monthly_savings * Decimal("12.0000")

        # Recommendation count across open opportunities
        rec_count_res = await session.execute(
            select(func.count(Recommendation.id))
            .join(OptimizationOpportunity, Recommendation.opportunity_id == OptimizationOpportunity.id)
            .where(
                OptimizationOpportunity.account_id.in_(tenant.account_ids),
                OptimizationOpportunity.status == "OPEN",
            )
        )
        rec_count = rec_count_res.scalar() or 0

        items = [cls._to_schema(o, tenant.account_name_map) for o in opps]

        return OptimizationOverviewResponse(
            potential_monthly_savings=potential_monthly_savings,
            potential_annual_savings=potential_annual_savings,
            opportunity_count=len(items),
            recommendation_count=rec_count,
            opportunities=items,
        )

    @classmethod
    async def get_opportunity_detail(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        opportunity_id: str,
    ) -> OpportunityItem:
        """Retrieves a single opportunity with all recommendations, scoped to tenant accounts."""
        query = (
            select(OptimizationOpportunity)
            .options(
                selectinload(OptimizationOpportunity.resource),
                selectinload(OptimizationOpportunity.recommendations),
            )
            .where(
                OptimizationOpportunity.id == opportunity_id,
                OptimizationOpportunity.account_id.in_(tenant.account_ids),
            )
        )
        result = await session.execute(query)
        opp = result.scalars().first()
        if not opp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization opportunity with ID '{opportunity_id}' not found in current organization context.",
            )
        return cls._to_schema(opp, tenant.account_name_map)
