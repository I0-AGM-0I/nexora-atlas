"""
NEXORA ATLAS - Forecast API Router
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.tenant import get_tenant_context
from app.services.forecast import ForecastService
from app.schemas.forecast import ForecastResponse

router = APIRouter(prefix="/forecast", tags=["Forecast"])


@router.get("", response_model=ForecastResponse, summary="Retrieve synthetic forecast horizons")
async def get_forecasts(
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> ForecastResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await ForecastService.get_forecasts(session, tenant)
