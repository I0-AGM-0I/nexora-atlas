"""
NEXORA ATLAS - Spend Service
Provides multidimensional spend exploration by date, service, account, and resource.
Strictly guarantees mathematical reconciliation with Dashboard KPIs.
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import List, Optional, Dict
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost import CostRecord
from app.models.resource import CloudResource
from app.services.tenant import TenantContext
from app.services.dashboard import DashboardService
from app.demo.events import get_demo_events
from app.schemas.dashboard import SpendTrendPoint, ServiceBreakdownItem, AccountBreakdownItem, DemoEventSchema
from app.schemas.spend import SpendExplorerResponse, ResourceSpendItem


class SpendService:
    @classmethod
    async def get_spend_explorer(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        period_days: int = 30,
        account_id: Optional[str] = None,
        service_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SpendExplorerResponse:
        """
        Retrieves spend metrics and paginated resource breakdown.
        Guarantees that filtering is applied uniformly across totals, trends, breakdowns, and tables.
        """
        _, max_date = await DashboardService.get_max_and_min_date(session, tenant.account_ids)
        start_date = max_date - timedelta(days=period_days - 1)

        # Target accounts
        target_accounts = [account_id] if account_id and account_id in tenant.account_ids else tenant.account_ids

        # Base filters
        base_conditions = [
            CostRecord.account_id.in_(target_accounts),
            CostRecord.usage_date >= start_date,
            CostRecord.usage_date <= max_date,
        ]
        if service_name:
            base_conditions.append(CostRecord.service_name == service_name)

        # 1. Total Spend in Period
        total_res = await session.execute(
            select(func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")))
            .where(*base_conditions)
        )
        total_spend = total_res.scalar() or Decimal("0.0000")

        # 2. Previous Period Spend (for identical duration)
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date - timedelta(days=1)
        prev_conditions = [
            CostRecord.account_id.in_(target_accounts),
            CostRecord.usage_date >= prev_start,
            CostRecord.usage_date <= prev_end,
        ]
        if service_name:
            prev_conditions.append(CostRecord.service_name == service_name)

        prev_res = await session.execute(
            select(func.coalesce(func.sum(CostRecord.unblended_cost), Decimal("0.0000")))
            .where(*prev_conditions)
        )
        prev_spend = prev_res.scalar() or Decimal("0.0000")

        period_change_pct: Optional[Decimal] = None
        if prev_spend > Decimal("0.0000"):
            period_change_pct = round(
                ((total_spend - prev_spend) / prev_spend) * Decimal("100.00"), 2
            )

        # 3. Daily Trend Points
        trend_query = (
            select(
                CostRecord.usage_date,
                func.sum(CostRecord.unblended_cost).label("daily_spend"),
            )
            .where(*base_conditions)
            .group_by(CostRecord.usage_date)
            .order_by(CostRecord.usage_date.asc())
        )
        trend_res = await session.execute(trend_query)
        trend_rows = trend_res.all()

        events_by_date: Dict[date, List[DemoEventSchema]] = {}
        if tenant.is_demo:
            for ev in get_demo_events():
                events_by_date.setdefault(ev.occurred_at, []).append(
                    DemoEventSchema(
                        id=ev.id,
                        occurred_at=ev.occurred_at.isoformat(),
                        title=ev.title,
                        description=ev.description,
                        category=ev.category,
                        impact_service=ev.impact_service,
                        related_resource_native_id=ev.related_resource_native_id,
                    )
                )

        trend_points: List[SpendTrendPoint] = []
        cum = Decimal("0.0000")
        for r in trend_rows:
            d_val = r.daily_spend or Decimal("0.0000")
            cum += d_val
            trend_points.append(
                SpendTrendPoint(
                    date=r.usage_date.isoformat(),
                    spend=d_val,
                    cumulative_spend=cum,
                    events=events_by_date.get(r.usage_date, []),
                )
            )

        # 4. Service Breakdown
        srv_query = (
            select(
                CostRecord.service_name,
                func.sum(CostRecord.unblended_cost).label("spend"),
            )
            .where(*base_conditions)
            .group_by(CostRecord.service_name)
            .order_by(func.sum(CostRecord.unblended_cost).desc())
        )
        srv_res = await session.execute(srv_query)
        service_items = [
            ServiceBreakdownItem(
                service_name=r.service_name,
                total_spend=r.spend,
                percentage=(
                    round((r.spend / total_spend) * Decimal("100.00"), 2)
                    if total_spend > Decimal("0.0000")
                    else Decimal("0.00")
                ),
            )
            for r in srv_res.all()
        ]

        # 5. Account Breakdown
        acc_query = (
            select(
                CostRecord.account_id,
                func.sum(CostRecord.unblended_cost).label("spend"),
            )
            .where(*base_conditions)
            .group_by(CostRecord.account_id)
            .order_by(func.sum(CostRecord.unblended_cost).desc())
        )
        acc_res = await session.execute(acc_query)
        acc_lookup = {a.id: a for a in tenant.accounts}
        account_items = [
            AccountBreakdownItem(
                account_id=r.account_id,
                account_name=acc_lookup[r.account_id].name if r.account_id in acc_lookup else "Unknown",
                provider_account_id=acc_lookup[r.account_id].account_id if r.account_id in acc_lookup else r.account_id,
                total_spend=r.spend,
                percentage=(
                    round((r.spend / total_spend) * Decimal("100.00"), 2)
                    if total_spend > Decimal("0.0000")
                    else Decimal("0.00")
                ),
            )
            for r in acc_res.all()
        ]

        # 6. Paginated Resource Spend
        # Group spend by resource_id
        res_spend_query = (
            select(
                CostRecord.resource_id,
                func.sum(CostRecord.unblended_cost).label("res_spend"),
            )
            .where(
                *base_conditions,
                CostRecord.resource_id.isnot(None),
            )
            .group_by(CostRecord.resource_id)
            .order_by(func.sum(CostRecord.unblended_cost).desc())
        )
        all_res_spend = (await session.execute(res_spend_query)).all()
        total_unique_resources = len(all_res_spend)

        # Slice for pagination
        offset = (page - 1) * page_size
        paged_res_spend = all_res_spend[offset : offset + page_size]
        paged_res_ids = [r.resource_id for r in paged_res_spend if r.resource_id]

        # Load resource entities
        res_entities: Dict[str, CloudResource] = {}
        if paged_res_ids:
            res_query = (
                select(CloudResource)
                .options(selectinload(CloudResource.region))
                .where(CloudResource.id.in_(paged_res_ids))
            )
            res_rows = (await session.execute(res_query)).scalars().all()
            res_entities = {r.id: r for r in res_rows}

        resource_items: List[ResourceSpendItem] = []
        for r in paged_res_spend:
            res_obj = res_entities.get(r.resource_id)
            if not res_obj:
                continue
            acc_name = acc_lookup.get(res_obj.account_id).name if res_obj.account_id in acc_lookup else "Unknown"
            pct = (
                round((r.res_spend / total_spend) * Decimal("100.00"), 2)
                if total_spend > Decimal("0.0000")
                else Decimal("0.00")
            )
            region_str = res_obj.region.region_code if res_obj.region else "unknown"
            resource_items.append(
                ResourceSpendItem(
                    resource_id=res_obj.id,
                    native_id=res_obj.native_id,
                    resource_name=res_obj.name or res_obj.native_id,
                    service_name=res_obj.service_name,
                    resource_type=res_obj.resource_type,
                    account_name=acc_name,
                    region=region_str,
                    spend=r.res_spend,
                    percentage_of_total=pct,
                )
            )

        total_pages = max(1, (total_unique_resources + page_size - 1) // page_size)

        return SpendExplorerResponse(
            period_days=period_days,
            start_date=start_date.isoformat(),
            end_date=max_date.isoformat(),
            total_spend=total_spend,
            previous_period_spend=prev_spend,
            period_change_pct=period_change_pct,
            currency=tenant.currency,
            trend=trend_points,
            service_breakdown=service_items,
            account_breakdown=account_items,
            resource_items=resource_items,
            total_resources=total_unique_resources,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
