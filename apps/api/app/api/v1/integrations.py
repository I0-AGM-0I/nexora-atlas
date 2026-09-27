from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.tenant import get_tenant_context, TenantContext
from app.services.integrations import IntegrationService
from app.schemas.integrations import (
    AWSConfigureRequest,
    AWSValidateRequest,
    IntegrationItemResponse,
    AWSValidationResponse,
    SyncJobItemResponse,
    IntegrationStatusResponse,
    SyncTriggerResponse,
)

router = APIRouter(prefix="/integrations", tags=["Cloud Integrations"])


@router.get(
    "",
    response_model=List[IntegrationItemResponse],
    summary="List all configured cloud integrations for tenant",
)
async def list_integrations(
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
):
    tenant = await get_tenant_context(session, org_slug)
    return await IntegrationService.list_integrations(session, tenant)


@router.get(
    "/{integration_id}",
    response_model=IntegrationItemResponse,
    summary="Get single integration by ID",
)
async def get_integration(
    integration_id: str,
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
):
    tenant = await get_tenant_context(session, org_slug)
    item = await IntegrationService.get_integration(session, tenant, integration_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration {integration_id} not found",
        )
    return item


@router.post(
    "/aws/configure",
    response_model=IntegrationItemResponse,
    summary="Configure or update customer AWS IAM connection",
)
async def configure_aws_integration(
    payload: AWSConfigureRequest,
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
):
    tenant = await get_tenant_context(session, org_slug)
    return await IntegrationService.configure_aws(session, tenant, payload)


@router.post(
    "/aws/validate",
    response_model=AWSValidationResponse,
    summary="Validate AWS IAM connection and read-only service permissions",
)
async def validate_aws_connection(
    payload: AWSValidateRequest,
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
):
    tenant = await get_tenant_context(session, org_slug)
    return await IntegrationService.validate_aws(session, tenant, payload)


@router.post(
    "/aws/sync",
    response_model=SyncTriggerResponse,
    summary="Trigger read-only synchronization from AWS",
)
async def trigger_aws_sync(
    integration_id: str,
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
):
    tenant = await get_tenant_context(session, org_slug)
    item = await IntegrationService.get_integration(session, tenant, integration_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration {integration_id} not found",
        )
    return await IntegrationService.trigger_sync(session, tenant, integration_id)


@router.get(
    "/{integration_id}/sync-jobs",
    response_model=List[SyncJobItemResponse],
    summary="Retrieve sync history for an integration",
)
async def list_sync_jobs(
    integration_id: str,
    limit: int = 20,
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
):
    tenant = await get_tenant_context(session, org_slug)
    return await IntegrationService.list_sync_jobs(session, tenant, integration_id, limit=limit)


@router.get(
    "/{integration_id}/status",
    response_model=IntegrationStatusResponse,
    summary="Retrieve health, freshness, and permission status for an integration",
)
async def get_integration_status(
    integration_id: str,
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
):
    tenant = await get_tenant_context(session, org_slug)
    status_obj = await IntegrationService.get_status(session, tenant, integration_id)
    if not status_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration {integration_id} not found",
        )
    return status_obj
