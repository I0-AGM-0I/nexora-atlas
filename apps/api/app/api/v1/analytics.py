"""
NEXORA ATLAS - Analytics API Router
Exposes deterministic trend analysis, cost drivers, concentration, efficiency, and portfolio modeling.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.tenant import get_tenant_context
from app.services.analytics import AnalyticsService
from app.schemas.analytics import (
    AnalyticsTrendsResponse,
    AnalyticsDriversResponse,
    AnalyticsConcentrationResponse,
    AnalyticsEfficiencyResponse,
    AnalyticsPortfolioResponse,
    AnalyticsSummaryResponse,
)
from app.schemas.telemetry import DataQualityReportResponse
from app.services.telemetry import TelemetryService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/trends", response_model=AnalyticsTrendsResponse)
async def get_trends(
    window: int = Query(30, ge=3, le=90, description="Comparison window in calendar days"),
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
):
    """Returns rolling daily averages, volatility metrics, and trend regime classification."""
    tenant = await get_tenant_context(session, org_slug)
    return await AnalyticsService.get_trends(session, tenant, comparison_window_days=window)


@router.get("/drivers", response_model=AnalyticsDriversResponse)
async def get_drivers(
    window: int = Query(30, ge=3, le=90, description="Comparison window in calendar days"),
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
):
    """Returns period-over-period spend decomposition across Service, Account, Resource, and Region dimensions."""
    tenant = await get_tenant_context(session, org_slug)
    return await AnalyticsService.get_drivers(session, tenant, comparison_window_days=window)


@router.get("/concentration", response_model=AnalyticsConcentrationResponse)
async def get_concentration(
    window: int = Query(30, ge=3, le=90, description="Comparison window in calendar days"),
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
):
    """Returns Top 1/3/5 spend shares and descriptive Spend Concentration Index (HHI)."""
    tenant = await get_tenant_context(session, org_slug)
    return await AnalyticsService.get_concentration(session, tenant, comparison_window_days=window)


@router.get("/efficiency", response_model=AnalyticsEfficiencyResponse)
async def get_efficiency(
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
):
    """Returns capacity headroom, idle resource run-rate spend, and unit economics contracts."""
    tenant = await get_tenant_context(session, org_slug)
    return await AnalyticsService.get_efficiency(session, tenant)


@router.get("/portfolio", response_model=AnalyticsPortfolioResponse)
async def get_portfolio(
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
):
    """Returns collective optimization portfolio, mutually exclusive conflicts, and dependency graphs."""
    tenant = await get_tenant_context(session, org_slug)
    return await AnalyticsService.get_portfolio(session, tenant)


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_summary(
    window: int = Query(30, ge=3, le=90, description="Comparison window in calendar days"),
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
):
    """Returns full analytical summary demonstrating the Dashboard -> Spend -> Driver -> Opportunity -> Scenario chain."""
    tenant = await get_tenant_context(session, org_slug)
    return await AnalyticsService.get_summary(session, tenant, comparison_window_days=window)


@router.get("/data-quality", response_model=DataQualityReportResponse)
async def get_data_quality(
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> DataQualityReportResponse:
    """Returns data trustworthiness and telemetry completeness metrics across all integrated accounts."""
    tenant = await get_tenant_context(session, org_slug)
    return await TelemetryService.get_data_quality_report(session, tenant)

