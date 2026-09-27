"""
NEXORA ATLAS - Resource Service
Manages cloud resource inventory exploration with 30-day attributed cost aggregation.
"""

from decimal import Decimal
from datetime import timedelta
from typing import List, Optional, Dict
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.resource import CloudResource, Tag
from app.models.account import CloudRegion
from app.models.cost import CostRecord
from app.services.tenant import TenantContext
from app.services.dashboard import DashboardService
from app.schemas.resource import ResourceListItem, ResourceListResponse


class ResourceService:
    @classmethod
    async def list_resources(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        search: Optional[str] = None,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
        service_name: Optional[str] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> ResourceListResponse:
        """Retrieves paginated cloud resources matching search and filter constraints."""
        target_accounts = [account_id] if account_id and account_id in tenant.account_ids else tenant.account_ids

        query = (
            select(CloudResource)
            .options(
                selectinload(CloudResource.tags),
                selectinload(CloudResource.region),
            )
            .where(CloudResource.account_id.in_(target_accounts))
        )

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    CloudResource.name.ilike(search_pattern),
                    CloudResource.native_id.ilike(search_pattern),
                    CloudResource.service_name.ilike(search_pattern),
                    CloudResource.resource_type.ilike(search_pattern),
                )
            )

        if region:
            query = query.join(CloudResource.region).where(CloudRegion.region_code == region)
        if service_name:
            query = query.where(CloudResource.service_name == service_name)
        if status_filter:
            query = query.where(CloudResource.status == status_filter.upper())

        # Total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await session.execute(count_query)).scalar() or 0

        # Pagination
        offset = (page - 1) * page_size
        paged_query = query.order_by(CloudResource.service_name.asc(), CloudResource.name.asc()).limit(page_size).offset(offset)
        result = await session.execute(paged_query)
        resources = list(result.scalars().all())

        # Calculate 30-day attributed costs for returned resources
        cost_30d_map: Dict[str, Decimal] = {}
        if resources:
            res_ids = [r.id for r in resources]
            _, max_date = await DashboardService.get_max_and_min_date(session, tenant.account_ids)
            latest_30_start = max_date - timedelta(days=29)

            cost_res = await session.execute(
                select(
                    CostRecord.resource_id,
                    func.sum(CostRecord.unblended_cost).label("spend_30d"),
                )
                .where(
                    CostRecord.resource_id.in_(res_ids),
                    CostRecord.usage_date >= latest_30_start,
                    CostRecord.usage_date <= max_date,
                )
                .group_by(CostRecord.resource_id)
            )
            for row in cost_res.all():
                if row.resource_id:
                    cost_30d_map[row.resource_id] = row.spend_30d

        items: List[ResourceListItem] = []
        for r in resources:
            tag_dict = {t.key: t.value for t in r.tags}
            region_str = r.region.region_code if r.region else "unknown"
            items.append(
                ResourceListItem(
                    id=r.id,
                    account_id=r.account_id,
                    account_name=tenant.account_name_map.get(r.account_id, "Unknown"),
                    region_code=region_str,
                    native_id=r.native_id,
                    name=r.name or r.native_id,
                    service_name=r.service_name,
                    resource_type=r.resource_type,
                    status=r.status,
                    tags=tag_dict,
                    cost_30d=cost_30d_map.get(r.id),
                )
            )

        total_pages = max(1, (total_count + page_size - 1) // page_size)
        return ResourceListResponse(
            items=items,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @classmethod
    async def get_resource(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        resource_id: str,
    ) -> ResourceListItem:
        """Retrieves a single resource with tags and 30-day cost, scoped to tenant."""
        query = (
            select(CloudResource)
            .options(
                selectinload(CloudResource.tags),
                selectinload(CloudResource.region),
            )
            .where(
                CloudResource.id == resource_id,
                CloudResource.account_id.in_(tenant.account_ids),
            )
        )
        result = await session.execute(query)
        res = result.scalars().first()
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource with ID '{resource_id}' not found in current organization context.",
            )

        _, max_date = await DashboardService.get_max_and_min_date(session, tenant.account_ids)
        latest_30_start = max_date - timedelta(days=29)

        cost_res = await session.execute(
            select(func.sum(CostRecord.unblended_cost))
            .where(
                CostRecord.resource_id == res.id,
                CostRecord.usage_date >= latest_30_start,
                CostRecord.usage_date <= max_date,
            )
        )
        cost_30d = cost_res.scalar()

        tag_dict = {t.key: t.value for t in res.tags}
        region_str = res.region.region_code if res.region else "unknown"
        return ResourceListItem(
            id=res.id,
            account_id=res.account_id,
            account_name=tenant.account_name_map.get(res.account_id, "Unknown"),
            region_code=region_str,
            native_id=res.native_id,
            name=res.name or res.native_id,
            service_name=res.service_name,
            resource_type=res.resource_type,
            status=res.status,
            tags=tag_dict,
            cost_30d=cost_30d,
        )
