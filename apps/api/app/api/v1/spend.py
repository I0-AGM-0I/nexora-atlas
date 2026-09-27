"""
NEXORA ATLAS - Spend Explorer API Router
Provides multidimensional spend exploration with filters, daily trend, breakdowns, and paginated table.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.tenant import get_tenant_context
from app.services.spend import SpendService
from app.schemas.spend import SpendExplorerResponse

router = APIRouter(prefix="/spend", tags=["Spend Explorer"])


@router.get("", response_model=SpendExplorerResponse, summary="Explore spend across time horizons, services, accounts, and resources")
@router.get("/explorer", response_model=SpendExplorerResponse, include_in_schema=False)
async def get_spend_explorer(
    period_days: int = Query(30, ge=7, le=365, description="Time window in days (e.g. 7, 30, 90)"),
    account_id: Optional[str] = Query(None, description="Filter by cloud account UUID"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> SpendExplorerResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await SpendService.get_spend_explorer(
        session=session,
        tenant=tenant,
        period_days=period_days,
        account_id=account_id,
        service_name=service_name,
        page=page,
        page_size=page_size,
    )
