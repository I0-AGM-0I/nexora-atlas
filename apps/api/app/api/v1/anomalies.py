"""
NEXORA ATLAS - Anomalies API Router
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.tenant import get_tenant_context
from app.services.anomaly import AnomalyService
from app.schemas.anomaly import AnomalyListResponse, AnomalyItem

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])


@router.get("", response_model=AnomalyListResponse, summary="List spending anomalies with observed facts vs inferred hypotheses")
async def list_anomalies(
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL | HIGH | MEDIUM | LOW"),
    status: Optional[str] = Query(None, description="Filter by status: OPEN | RESOLVED | ACKNOWLEDGED"),
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> AnomalyListResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await AnomalyService.list_anomalies(session, tenant, severity=severity, status_filter=status)


@router.get("/{anomaly_id}", response_model=AnomalyItem, summary="Get single anomaly detail with separated observed/inferred metrics")
async def get_anomaly_detail(
    anomaly_id: str,
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> AnomalyItem:
    tenant = await get_tenant_context(session, org_slug)
    return await AnomalyService.get_anomaly(session, tenant, anomaly_id=anomaly_id)
