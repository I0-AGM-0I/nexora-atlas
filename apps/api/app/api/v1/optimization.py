"""
NEXORA ATLAS - Optimization API Router
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.tenant import get_tenant_context
from app.services.optimization import OptimizationService
from app.schemas.optimization import OptimizationOverviewResponse, OpportunityItem

router = APIRouter(prefix="/optimization", tags=["Optimization"])


@router.get("", response_model=OptimizationOverviewResponse, summary="List optimization opportunities and potential savings")
@router.get("/overview", response_model=OptimizationOverviewResponse, include_in_schema=False)
async def get_optimization_overview(
    category: Optional[str] = Query(None, description="Filter by category (e.g. COMPUTE, STORAGE, DATABASE)"),
    severity: Optional[str] = Query(None, description="Filter by severity: HIGH | MEDIUM | LOW"),
    status: Optional[str] = Query("OPEN", description="Filter by status: OPEN | IMPLEMENTED | DISMISSED"),
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> OptimizationOverviewResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await OptimizationService.get_overview(session, tenant, category=category, severity=severity, status_filter=status)


@router.get("/{opportunity_id}", response_model=OpportunityItem, summary="Get single opportunity detail with recommendations")
async def get_opportunity_detail(
    opportunity_id: str,
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> OpportunityItem:
    tenant = await get_tenant_context(session, org_slug)
    return await OptimizationService.get_opportunity_detail(session, tenant, opportunity_id=opportunity_id)
