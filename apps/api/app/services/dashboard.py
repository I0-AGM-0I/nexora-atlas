"""
NEXORA ATLAS - Dashboard Service
Aggregates technology cost intelligence, spending trends, service/account breakdowns,
anomalies, and optimization metrics for the primary executive command center.
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost import CostRecord
from app.models.anomaly import Anomaly
from app.models.optimization import OptimizationOpportunity
from app.models.resource import CloudResource
from app.models.organization import AuditLog
from app.services.tenant import TenantContext
from app.demo.events import get_demo_events
from app.schemas.dashboard import (
    DashboardSummary,
    SpendTrendPoint,
    SpendTrendResponse,
    ServiceBreakdownItem,
    ServiceBreakdownResponse,
    AccountBreakdownItem,
    AccountBreakdownResponse,
    RecentActivityItem,
    RecentActivityResponse,
    DemoEventSchema,
)


class DashboardService:
    @staticmethod
    async def get_max_and_min_date(session: AsyncSession, account_ids: List[str]) -> tuple[date, date]:
        """Resolves the valid dataset date window from persisted CostRecords."""
        res = await session.execute(
            select(
                func.min(CostRecord.usage_date).label("min_date"),
                func.max(CostRecord.usage_date).label("max_date"),
            ).where(CostRecord.account_id.in_(account_ids))
        )
        row = res.first()
        if not row or not row.max_date or not row.min_date:
            today = date.today()
            return today - timedelta(days=89), today
        return row.min_date, row.max_date

    @classmethod
    async def get_summary(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
    ) -> DashboardSummary:
        """
        Computes high-level financial KPIs:
        - Total Historical Spend: Sum of all CostRecords in dataset
        - Monthly Run Rate: Sum of CostRecords over latest 30 calendar days
        - Previous 30-Day Spend: Sum of CostRecords from day -60 to -31
        - Potential Monthly Savings: Sum of active OptimizationOpportunity records
        - Active Anomalies: Count of OPEN anomalies
        """
        min_date, max_date = await cls.get_max_and_min_date(session, tenant.account_ids)

        # 1. Total Spend across all records
        total_spend_res = await session.execute(
            select(func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")))
            .where(CostRecord.account_id.in_(tenant.account_ids))
        )
        total_spend = total_spend_res.scalar() or Decimal("0.0000")

        # 2. Latest 30 days window [max_date - 29 days, max_date]
        latest_30_start = max_date - timedelta(days=29)
        mrr_res = await session.execute(
            select(func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")))
            .where(
                CostRecord.account_id.in_(tenant.account_ids),
                CostRecord.usage_date >= latest_30_start,
                CostRecord.usage_date <= max_date,
            )
        )
        monthly_run_rate = mrr_res.scalar() or Decimal("0.0000")

        # 3. Previous 30 days window [max_date - 59 days, max_date - 30 days]
        prev_30_start = max_date - timedelta(days=59)
        prev_30_end = max_date - timedelta(days=30)
        prev_mrr_res = await session.execute(
            select(func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")))
            .where(
                CostRecord.account_id.in_(tenant.account_ids),
                CostRecord.usage_date >= prev_30_start,
                CostRecord.usage_date <= prev_30_end,
            )
        )
        prev_30_spend = prev_mrr_res.scalar() or Decimal("0.0000")

        # Period-over-period delta calculation
        run_rate_change_pct: Optional[Decimal] = None
        if prev_30_spend > Decimal("0.0000"):
            run_rate_change_pct = round(
                ((monthly_run_rate - prev_30_spend) / prev_30_spend) * Decimal("100.00"), 2
            )

        # 4. Potential Monthly Savings
        savings_res = await session.execute(
            select(func.coalesce(func.sum(OptimizationOpportunity.estimated_waste_monthly), Decimal("0.0000")))
            .where(
                OptimizationOpportunity.account_id.in_(tenant.account_ids),
                OptimizationOpportunity.status == "OPEN",
            )
        )
        potential_monthly_savings = savings_res.scalar() or Decimal("0.0000")
        potential_annual_savings = potential_monthly_savings * Decimal("12.0000")

        # 5. Active Anomalies Count (OPEN or ACKNOWLEDGED)
        anomalies_count_res = await session.execute(
            select(func.count(Anomaly.id))
            .where(
                Anomaly.account_id.in_(tenant.account_ids),
                Anomaly.status.in_(["OPEN", "ACKNOWLEDGED"]),
            )
        )
        active_anomalies = anomalies_count_res.scalar() or 0

        # 6. Total Resources Count
        res_count_res = await session.execute(
            select(func.count(CloudResource.id))
            .where(CloudResource.account_id.in_(tenant.account_ids))
        )
        total_resources = res_count_res.scalar() or 0

        return DashboardSummary(
            organization_name=tenant.org_name,
            total_spend=total_spend,
            monthly_run_rate=monthly_run_rate,
            previous_30d_spend=prev_30_spend,
            run_rate_change_pct=run_rate_change_pct,
            potential_monthly_savings=potential_monthly_savings,
            potential_annual_savings=potential_annual_savings,
            active_anomalies=active_anomalies,
            total_resources=total_resources,
            total_accounts=len(tenant.account_ids),
            currency=tenant.currency,
            max_date=max_date.isoformat(),
            min_date=min_date.isoformat(),
            is_demo=tenant.is_demo,
        )

    @classmethod
    async def get_spend_trend(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        days: int = 90,
    ) -> SpendTrendResponse:
        """
        Retrieves daily aggregated spend over the specified window (default 90 days),
        with cumulative progression and domain event annotations.
        """
        _, max_date = await cls.get_max_and_min_date(session, tenant.account_ids)
        start_date = max_date - timedelta(days=days - 1)

        query = (
            select(
                CostRecord.usage_date,
                func.sum(CostRecord.unblended_cost).label("daily_spend"),
            )
            .where(
                CostRecord.account_id.in_(tenant.account_ids),
                CostRecord.usage_date >= start_date,
                CostRecord.usage_date <= max_date,
            )
            .group_by(CostRecord.usage_date)
            .order_by(CostRecord.usage_date.asc())
        )
        result = await session.execute(query)
        rows = result.all()

        # Map domain events by date
        events_by_date: Dict[date, List[DemoEventSchema]] = {}
        if tenant.is_demo:
            for ev in get_demo_events():
                ev_schema = DemoEventSchema(
                    id=ev.id,
                    occurred_at=ev.occurred_at.isoformat(),
                    title=ev.title,
                    description=ev.description,
                    category=ev.category,
                    impact_service=ev.impact_service,
                    related_resource_native_id=ev.related_resource_native_id,
                )
                events_by_date.setdefault(ev.occurred_at, []).append(ev_schema)

        points: List[SpendTrendPoint] = []
        cumulative = Decimal("0.0000")
        total_spend = Decimal("0.0000")

        for row in rows:
            daily_val = row.daily_spend or Decimal("0.0000")
            cumulative += daily_val
            total_spend += daily_val
            ev_list = events_by_date.get(row.usage_date, [])
            points.append(
                SpendTrendPoint(
                    date=row.usage_date.isoformat(),
                    spend=daily_val,
                    cumulative_spend=cumulative,
                    events=ev_list,
                )
            )

        return SpendTrendResponse(
            points=points,
            total_spend=total_spend,
            period_days=days,
            currency=tenant.currency,
        )

    @classmethod
    async def get_service_breakdown(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        days: int = 30,
    ) -> ServiceBreakdownResponse:
        """Computes cost breakdown by cloud service for the latest N days (default 30)."""
        _, max_date = await cls.get_max_and_min_date(session, tenant.account_ids)
        start_date = max_date - timedelta(days=days - 1)

        query = (
            select(
                CostRecord.service_name,
                func.sum(CostRecord.unblended_cost).label("service_spend"),
            )
            .where(
                CostRecord.account_id.in_(tenant.account_ids),
                CostRecord.usage_date >= start_date,
                CostRecord.usage_date <= max_date,
            )
            .group_by(CostRecord.service_name)
            .order_by(func.sum(CostRecord.unblended_cost).desc())
        )
        result = await session.execute(query)
        rows = result.all()

        total_window_spend = sum((r.service_spend for r in rows), Decimal("0.0000"))
        items: List[ServiceBreakdownItem] = []

        for r in rows:
            pct = (
                round((r.service_spend / total_window_spend) * Decimal("100.00"), 2)
                if total_window_spend > Decimal("0.0000")
                else Decimal("0.00")
            )
            items.append(
                ServiceBreakdownItem(
                    service_name=r.service_name,
                    total_spend=r.service_spend,
                    percentage=pct,
                )
            )

        return ServiceBreakdownResponse(
            items=items,
            total_spend=total_window_spend,
            currency=tenant.currency,
        )

    @classmethod
    async def get_account_breakdown(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        days: int = 30,
    ) -> AccountBreakdownResponse:
        """Computes cost breakdown by cloud account for the latest N days (default 30)."""
        _, max_date = await cls.get_max_and_min_date(session, tenant.account_ids)
        start_date = max_date - timedelta(days=days - 1)

        query = (
            select(
                CostRecord.account_id,
                func.sum(CostRecord.unblended_cost).label("account_spend"),
            )
            .where(
                CostRecord.account_id.in_(tenant.account_ids),
                CostRecord.usage_date >= start_date,
                CostRecord.usage_date <= max_date,
            )
            .group_by(CostRecord.account_id)
            .order_by(func.sum(CostRecord.unblended_cost).desc())
        )
        result = await session.execute(query)
        rows = result.all()

        total_window_spend = sum((r.account_spend for r in rows), Decimal("0.0000"))
        items: List[AccountBreakdownItem] = []

        acc_lookup = {acc.id: acc for acc in tenant.accounts}

        for r in rows:
            acc = acc_lookup.get(r.account_id)
            acc_name = acc.name if acc else "Unknown Account"
            provider_acc_id = acc.account_id if acc else r.account_id
            pct = (
                round((r.account_spend / total_window_spend) * Decimal("100.00"), 2)
                if total_window_spend > Decimal("0.0000")
                else Decimal("0.00")
            )
            items.append(
                AccountBreakdownItem(
                    account_id=r.account_id,
                    account_name=acc_name,
                    provider_account_id=provider_acc_id,
                    total_spend=r.account_spend,
                    percentage=pct,
                )
            )

        return AccountBreakdownResponse(
            items=items,
            total_spend=total_window_spend,
            currency=tenant.currency,
        )

    @classmethod
    async def get_recent_activity(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        limit: int = 8,
    ) -> RecentActivityResponse:
        """Returns chronological audit events from AuditLog table."""
        query = (
            select(AuditLog)
            .where(AuditLog.org_id == tenant.org_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        logs = list(result.scalars().all())

        items = [
            RecentActivityItem(
                id=log.id,
                timestamp=log.timestamp.isoformat(),
                action=log.action,
                entity_type=log.entity_type,
                actor_id=log.actor_id,
                metadata_json=log.metadata_json,
            )
            for log in logs
        ]

        return RecentActivityResponse(items=items)
