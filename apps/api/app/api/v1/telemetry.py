"""
NEXORA ATLAS - Operational Telemetry API Router
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.tenant import get_tenant_context
from app.services.telemetry import TelemetryService
from app.schemas.telemetry import (
    ResourceTelemetryResponse,
    IntegrationTelemetryStatusResponse,
)
from app.schemas.integrations import SyncTriggerResponse

router = APIRouter(tags=["Operational Telemetry"])


@router.get(
    "/resources/{resource_id}/telemetry",
    response_model=ResourceTelemetryResponse,
    summary="Get operational telemetry observations and statistical rollups for a resource",
)
async def get_resource_telemetry(
    resource_id: str,
    days: int = Query(30, ge=1, le=90, description="Window size in calendar days"),
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> ResourceTelemetryResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await TelemetryService.get_resource_telemetry(
        session=session,
        tenant=tenant,
        resource_id=resource_id,
        days=days,
    )


@router.get(
    "/integrations/{integration_id}/telemetry/status",
    response_model=IntegrationTelemetryStatusResponse,
    summary="Get operational telemetry sync health, coverage, and capabilities for an integration",
)
async def get_integration_telemetry_status(
    integration_id: str,
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> IntegrationTelemetryStatusResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await TelemetryService.get_integration_telemetry_status(
        session=session,
        tenant=tenant,
        integration_id=integration_id,
    )


@router.post(
    "/integrations/aws/telemetry-sync",
    response_model=SyncTriggerResponse,
    summary="Trigger an on-demand operational telemetry synchronization",
)
async def trigger_telemetry_sync(
    integration_id: str,
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> SyncTriggerResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await TelemetryService.trigger_telemetry_sync(
        session=session,
        tenant=tenant,
        integration_id=integration_id,
    )
