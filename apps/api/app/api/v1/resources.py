"""
NEXORA ATLAS - Resources API Router
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.tenant import get_tenant_context
from app.services.resource import ResourceService
from app.schemas.resource import ResourceListResponse, ResourceListItem

router = APIRouter(prefix="/resources", tags=["Resource Inventory"])


@router.get("", response_model=ResourceListResponse, summary="List and search cloud resources with 30-day attributed costs")
async def list_resources(
    search: Optional[str] = Query(None, description="Search across name, native ID, service, or type"),
    account_id: Optional[str] = Query(None, description="Filter by account UUID"),
    region: Optional[str] = Query(None, description="Filter by AWS region"),
    service_name: Optional[str] = Query(None, description="Filter by AWS service name"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. ACTIVE, STOPPED)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> ResourceListResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await ResourceService.list_resources(
        session=session,
        tenant=tenant,
        search=search,
        account_id=account_id,
        region=region,
        service_name=service_name,
        status_filter=status,
        page=page,
        page_size=page_size,
    )


@router.get("/{resource_id}", response_model=ResourceListItem, summary="Get single resource details with tags and 30-day cost")
async def get_resource_detail(
    resource_id: str,
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> ResourceListItem:
    tenant = await get_tenant_context(session, org_slug)
    return await ResourceService.get_resource(session, tenant, resource_id=resource_id)
