"""
NEXORA ATLAS - Dashboard API Router
Provides executive financial command center endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.tenant import get_tenant_context, TenantContext
from app.services.dashboard import DashboardService
from app.services.anomaly import AnomalyService
from app.services.optimization import OptimizationService
from app.schemas.dashboard import (
    DashboardSummary,
    SpendTrendResponse,
    ServiceBreakdownResponse,
    AccountBreakdownResponse,
    RecentActivityResponse,
)
from app.schemas.anomaly import AnomalyListResponse
from app.schemas.optimization import OptimizationOverviewResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary, summary="Retrieve top-level financial KPIs")
async def get_dashboard_summary(
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> DashboardSummary:
    tenant = await get_tenant_context(session, org_slug)
    return await DashboardService.get_summary(session, tenant)


@router.get("/spend-trend", response_model=SpendTrendResponse, summary="Retrieve 90-day daily spend trend with event annotations")
async def get_spend_trend(
    days: int = Query(90, ge=7, le=365, description="Number of historical days"),
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> SpendTrendResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await DashboardService.get_spend_trend(session, tenant, days=days)


@router.get("/service-breakdown", response_model=ServiceBreakdownResponse, summary="Retrieve spend grouped by cloud service")
async def get_service_breakdown(
    days: int = Query(30, ge=1, le=365, description="Aggregation window in days"),
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> ServiceBreakdownResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await DashboardService.get_service_breakdown(session, tenant, days=days)


@router.get("/account-breakdown", response_model=AccountBreakdownResponse, summary="Retrieve spend grouped by cloud account")
async def get_account_breakdown(
    days: int = Query(30, ge=1, le=365, description="Aggregation window in days"),
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> AccountBreakdownResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await DashboardService.get_account_breakdown(session, tenant, days=days)


@router.get("/anomalies", response_model=AnomalyListResponse, summary="Retrieve top anomalies for dashboard preview")
async def get_dashboard_anomalies(
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> AnomalyListResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await AnomalyService.list_anomalies(session, tenant, status_filter="OPEN")


@router.get("/optimization", response_model=OptimizationOverviewResponse, summary="Retrieve optimization preview for dashboard")
async def get_dashboard_optimization(
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> OptimizationOverviewResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await OptimizationService.get_overview(session, tenant, status_filter="OPEN")


@router.get("/recent-activity", response_model=RecentActivityResponse, summary="Retrieve chronological audit activity feed")
async def get_recent_activity(
    limit: int = Query(8, ge=1, le=50, description="Max audit entries to return"),
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> RecentActivityResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await DashboardService.get_recent_activity(session, tenant, limit=limit)
