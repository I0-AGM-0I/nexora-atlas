"""
NEXORA ATLAS - Analytics Service Layer
Assembles data from database models and executes the deterministic AnalyticsEngine.
Strictly guarantees tenant isolation and financial reconciliation.
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost import CostRecord
from app.models.resource import CloudResource
from app.models.account import CloudAccount, CloudRegion
from app.models.optimization import OptimizationOpportunity, Recommendation
from app.services.tenant import TenantContext
from app.services.dashboard import DashboardService
from app.analytics.constants import DEFAULT_COMPARISON_WINDOW_DAYS
from app.analytics.orchestration.engine import AnalyticsEngine
from app.analytics.trends import TrendAnalyzer
from app.analytics.drivers import CostDriverAnalyzer
from app.analytics.efficiency import EfficiencyAnalyzer
from app.analytics.optimization import OptimizationPortfolio
from app.schemas.analytics import (
    AnalyticsTrendsResponse,
    AnalyticsDriversResponse,
    AnalyticsConcentrationResponse,
    AnalyticsEfficiencyResponse,
    AnalyticsPortfolioResponse,
    AnalyticsSummaryResponse,
)


class AnalyticsService:
    """Service layer providing deterministic analytics and scenario simulations."""

    @classmethod
    async def _get_daily_spend(
        cls,
        session: AsyncSession,
        account_ids: List[str],
    ) -> List[Tuple[date, Decimal]]:
        """Queries daily unblended spend chronological series."""
        res = await session.execute(
            select(
                CostRecord.usage_date,
                func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")).label("daily_cost"),
            )
            .where(CostRecord.account_id.in_(account_ids))
            .group_by(CostRecord.usage_date)
            .order_by(CostRecord.usage_date.asc())
        )
        return [(row.usage_date, row.daily_cost) for row in res.all()]

    @classmethod
    async def _get_period_records(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        comparison_window_days: int = DEFAULT_COMPARISON_WINDOW_DAYS,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Computes period-over-period spend for Services, Accounts, Resources, and Regions.
        Window 1 (Current): [max_date - W + 1, max_date]
        Window 2 (Previous): [max_date - 2W + 1, max_date - W]
        """
        _, max_date = await DashboardService.get_max_and_min_date(session, tenant.account_ids)
        curr_start = max_date - timedelta(days=comparison_window_days - 1)
        prev_start = max_date - timedelta(days=2 * comparison_window_days - 1)
        prev_end = max_date - timedelta(days=comparison_window_days)

        # 1. Service Records
        curr_svc_res = await session.execute(
            select(
                CostRecord.service_name,
                func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")).label("cost"),
            )
            .where(
                CostRecord.account_id.in_(tenant.account_ids),
                CostRecord.usage_date >= curr_start,
                CostRecord.usage_date <= max_date,
            )
            .group_by(CostRecord.service_name)
        )
        curr_services = {row.service_name: row.cost for row in curr_svc_res.all()}

        prev_svc_res = await session.execute(
            select(
                CostRecord.service_name,
                func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")).label("cost"),
            )
            .where(
                CostRecord.account_id.in_(tenant.account_ids),
                CostRecord.usage_date >= prev_start,
                CostRecord.usage_date <= prev_end,
            )
            .group_by(CostRecord.service_name)
        )
        prev_services = {row.service_name: row.cost for row in prev_svc_res.all()}

        all_services = sorted(set(curr_services.keys()) | set(prev_services.keys()))
        service_records = [
            {
                "id": s,
                "name": s,
                "current_cost": curr_services.get(s, Decimal("0.0000")),
                "previous_cost": prev_services.get(s, Decimal("0.0000")),
            }
            for s in all_services
        ]

        # 2. Account Records
        acc_name_map = tenant.account_name_map
        curr_acc_res = await session.execute(
            select(
                CostRecord.account_id,
                func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")).label("cost"),
            )
            .where(
                CostRecord.account_id.in_(tenant.account_ids),
                CostRecord.usage_date >= curr_start,
                CostRecord.usage_date <= max_date,
            )
            .group_by(CostRecord.account_id)
        )
        curr_accounts = {row.account_id: row.cost for row in curr_acc_res.all()}

        prev_acc_res = await session.execute(
            select(
                CostRecord.account_id,
                func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")).label("cost"),
            )
            .where(
                CostRecord.account_id.in_(tenant.account_ids),
                CostRecord.usage_date >= prev_start,
                CostRecord.usage_date <= prev_end,
            )
            .group_by(CostRecord.account_id)
        )
        prev_accounts = {row.account_id: row.cost for row in prev_acc_res.all()}

        all_accounts = sorted(set(curr_accounts.keys()) | set(prev_accounts.keys()))
        account_records = [
            {
                "id": a,
                "name": acc_name_map.get(a, a),
                "current_cost": curr_accounts.get(a, Decimal("0.0000")),
                "previous_cost": prev_accounts.get(a, Decimal("0.0000")),
            }
            for a in all_accounts
        ]

        # 3. Resource Records
        curr_res_q = await session.execute(
            select(
                CostRecord.resource_id,
                func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")).label("cost"),
            )
            .where(
                CostRecord.account_id.in_(tenant.account_ids),
                CostRecord.resource_id.is_not(None),
                CostRecord.usage_date >= curr_start,
                CostRecord.usage_date <= max_date,
            )
            .group_by(CostRecord.resource_id)
        )
        curr_resources = {row.resource_id: row.cost for row in curr_res_q.all()}

        prev_res_q = await session.execute(
            select(
                CostRecord.resource_id,
                func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")).label("cost"),
            )
            .where(
                CostRecord.account_id.in_(tenant.account_ids),
                CostRecord.resource_id.is_not(None),
                CostRecord.usage_date >= prev_start,
                CostRecord.usage_date <= prev_end,
            )
            .group_by(CostRecord.resource_id)
        )
        prev_resources = {row.resource_id: row.cost for row in prev_res_q.all()}

        all_res_ids = set(curr_resources.keys()) | set(prev_resources.keys())
        res_info_q = await session.execute(
            select(CloudResource).where(CloudResource.id.in_(list(all_res_ids)))
        )
        res_info_map = {r.id: r for r in res_info_q.scalars().all()}

        resource_records = [
            {
                "id": rid,
                "name": res_info_map[rid].name if rid in res_info_map else rid,
                "service_name": res_info_map[rid].service_name if rid in res_info_map else "Unknown",
                "current_cost": curr_resources.get(rid, Decimal("0.0000")),
                "previous_cost": prev_resources.get(rid, Decimal("0.0000")),
                "current_spec": str(res_info_map[rid].specs_json.get("instance_type")) if rid in res_info_map and res_info_map[rid].specs_json else None,
                "previous_spec": str(res_info_map[rid].specs_json.get("instance_type")) if rid in res_info_map and res_info_map[rid].specs_json else None,
            }
            for rid in all_res_ids
        ]

        # 4. Region Records
        curr_reg_res = await session.execute(
            select(
                func.coalesce(CloudRegion.region_code, "global").label("region"),
                func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")).label("cost"),
            )
            .outerjoin(CloudResource, CostRecord.resource_id == CloudResource.id)
            .outerjoin(CloudRegion, CloudResource.region_id == CloudRegion.id)
            .where(
                CostRecord.account_id.in_(tenant.account_ids),
                CostRecord.usage_date >= curr_start,
                CostRecord.usage_date <= max_date,
            )
            .group_by(func.coalesce(CloudRegion.region_code, "global"))
        )
        curr_regions = {row.region: row.cost for row in curr_reg_res.all()}

        prev_reg_res = await session.execute(
            select(
                func.coalesce(CloudRegion.region_code, "global").label("region"),
                func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")).label("cost"),
            )
            .outerjoin(CloudResource, CostRecord.resource_id == CloudResource.id)
            .outerjoin(CloudRegion, CloudResource.region_id == CloudRegion.id)
            .where(
                CostRecord.account_id.in_(tenant.account_ids),
                CostRecord.usage_date >= prev_start,
                CostRecord.usage_date <= prev_end,
            )
            .group_by(func.coalesce(CloudRegion.region_code, "global"))
        )
        prev_regions = {row.region: row.cost for row in prev_reg_res.all()}

        all_regions = sorted(set(curr_regions.keys()) | set(prev_regions.keys()))
        region_records = [
            {
                "id": r,
                "name": r,
                "current_cost": curr_regions.get(r, Decimal("0.0000")),
                "previous_cost": prev_regions.get(r, Decimal("0.0000")),
            }
            for r in all_regions
        ]

        return service_records, account_records, resource_records, region_records

    @classmethod
    async def _get_opportunities_and_recommendations(
        cls,
        session: AsyncSession,
        account_ids: List[str],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Queries Phase 5 opportunities and recommendations."""
        res = await session.execute(
            select(OptimizationOpportunity)
            .options(
                selectinload(OptimizationOpportunity.recommendations),
                selectinload(OptimizationOpportunity.resource),
            )
            .where(
                OptimizationOpportunity.account_id.in_(account_ids),
                OptimizationOpportunity.status == "OPEN",
            )
        )
        opps = res.scalars().all()

        opp_dicts: List[Dict[str, Any]] = []
        rec_dicts: List[Dict[str, Any]] = []

        for opp in opps:
            opp_dicts.append(
                {
                    "id": opp.id,
                    "account_id": opp.account_id,
                    "resource_id": opp.resource_id,
                    "waste_type": opp.waste_type,
                    "category": opp.category,
                    "severity": opp.severity,
                    "estimated_waste_monthly": opp.estimated_waste_monthly,
                    "evidence_json": opp.evidence_json,
                }
            )
            for r in opp.recommendations:
                rec_dicts.append(
                    {
                        "id": r.id,
                        "opportunity_id": r.opportunity_id,
                        "resource_id": r.resource_id or opp.resource_id,
                        "resource_name": opp.resource.name if opp.resource else None,
                        "title": r.title,
                        "category": r.category,
                        "current_configuration": r.current_configuration,
                        "recommended_configuration": r.recommended_configuration,
                        "estimated_monthly_savings": r.estimated_monthly_savings,
                        "estimated_annual_savings": r.estimated_annual_savings,
                        "confidence_pct": r.confidence_pct,
                        "risk_level": r.risk_level,
                        "reasoning": r.reasoning,
                        "current_monthly_cost": opp.estimated_waste_monthly,
                    }
                )

        return opp_dicts, rec_dicts

    @classmethod
    async def get_trends(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        comparison_window_days: int = DEFAULT_COMPARISON_WINDOW_DAYS,
    ) -> AnalyticsTrendsResponse:
        daily_records = await cls._get_daily_spend(session, tenant.account_ids)
        trends = TrendAnalyzer.analyze(daily_records, comparison_window_days)
        return AnalyticsTrendsResponse(trends=trends)

    @classmethod
    async def get_drivers(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        comparison_window_days: int = DEFAULT_COMPARISON_WINDOW_DAYS,
    ) -> AnalyticsDriversResponse:
        svc_recs, acc_recs, res_recs, reg_recs = await cls._get_period_records(
            session, tenant, comparison_window_days
        )
        drivers = CostDriverAnalyzer.decompose(
            service_records=svc_recs,
            account_records=acc_recs,
            resource_records=res_recs,
            region_records=reg_recs,
            comparison_window_days=comparison_window_days,
        )
        return AnalyticsDriversResponse(drivers=drivers)

    @classmethod
    async def get_concentration(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        comparison_window_days: int = DEFAULT_COMPARISON_WINDOW_DAYS,
    ) -> AnalyticsConcentrationResponse:
        svc_recs, acc_recs, res_recs, _ = await cls._get_period_records(
            session, tenant, comparison_window_days
        )
        concentration = CostDriverAnalyzer.calculate_concentration(
            service_records=svc_recs,
            account_records=acc_recs,
            resource_records=res_recs,
        )
        return AnalyticsConcentrationResponse(concentration=concentration)

    @classmethod
    async def get_efficiency(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
    ) -> AnalyticsEfficiencyResponse:
        res_q = await session.execute(
            select(CloudResource).where(CloudResource.account_id.in_(tenant.account_ids))
        )
        resources = [
            {
                "id": r.id,
                "name": r.name,
                "service_name": r.service_name,
                "specs_json": r.specs_json,
            }
            for r in res_q.scalars().all()
        ]
        opp_dicts, _ = await cls._get_opportunities_and_recommendations(session, tenant.account_ids)
        efficiency = EfficiencyAnalyzer.analyze(
            resources=resources,
            phase5_opportunities=opp_dicts,
        )
        return AnalyticsEfficiencyResponse(efficiency=efficiency)

    @classmethod
    async def get_portfolio(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
    ) -> AnalyticsPortfolioResponse:
        opp_dicts, rec_dicts = await cls._get_opportunities_and_recommendations(
            session, tenant.account_ids
        )
        portfolio = OptimizationPortfolio.evaluate(
            opportunities=opp_dicts,
            recommendations=rec_dicts,
        )
        return AnalyticsPortfolioResponse(portfolio=portfolio)

    @classmethod
    async def get_summary(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        comparison_window_days: int = DEFAULT_COMPARISON_WINDOW_DAYS,
    ) -> AnalyticsSummaryResponse:
        daily_records = await cls._get_daily_spend(session, tenant.account_ids)
        svc_recs, acc_recs, res_recs, reg_recs = await cls._get_period_records(
            session, tenant, comparison_window_days
        )
        res_q = await session.execute(
            select(CloudResource).where(CloudResource.account_id.in_(tenant.account_ids))
        )
        resources_inventory = [
            {
                "id": r.id,
                "name": r.name,
                "service_name": r.service_name,
                "specs_json": r.specs_json,
            }
            for r in res_q.scalars().all()
        ]
        opp_dicts, rec_dicts = await cls._get_opportunities_and_recommendations(
            session, tenant.account_ids
        )

        full_analytics = AnalyticsEngine.run_full_analytics(
            daily_records=daily_records,
            service_records=svc_recs,
            account_records=acc_recs,
            resource_records=res_recs,
            region_records=reg_recs,
            resources_inventory=resources_inventory,
            phase5_opportunities=opp_dicts,
            phase5_recommendations=rec_dicts,
            comparison_window_days=comparison_window_days,
        )

        return AnalyticsSummaryResponse(
            trends=full_analytics["trends"],
            drivers=full_analytics["drivers"],
            concentration=full_analytics["concentration"],
            efficiency=full_analytics["efficiency"],
            portfolio=full_analytics["portfolio"],
            scenarios=full_analytics["scenarios"],
            chain_summary=full_analytics["chain_summary"],
        )
