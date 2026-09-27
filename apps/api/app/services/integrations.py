"""
NEXORA ATLAS - Integration Service Layer
Handles tenant-scoped configuration, connection validation, and sync orchestration.
Strictly sanitizes all outputs to prevent credential or External ID disclosure.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Integration, SyncJob
from app.services.tenant import TenantContext
from app.schemas.integrations import (
    AWSConfigureRequest,
    AWSValidateRequest,
    IntegrationItemResponse,
    AWSValidationResponse,
    SyncJobItemResponse,
    IntegrationStatusResponse,
    SyncTriggerResponse,
)
from app.integrations.providers.base import AWSServicePermissions, PermissionStatus
from app.integrations.providers.aws.client import AWSClientFactory
from app.integrations.providers.aws.auth import AWSAuthenticator
from app.integrations.sync.coordinator import SyncCoordinator

logger = logging.getLogger("atlas.services.integrations")


class IntegrationService:
    """Domain service managing cloud integrations and sync jobs."""

    @staticmethod
    def _mask_role_arn(role_arn: Optional[str]) -> Optional[str]:
        if not role_arn:
            return None
        parts = role_arn.split(":")
        if len(parts) >= 6:
            parts[4] = "***"
            return ":".join(parts)
        return f"...{role_arn[-12:]}"

    @classmethod
    def _to_sanitized_response(cls, item: Integration) -> IntegrationItemResponse:
        cfg = item.config_json or {}
        role_arn = cfg.get("role_arn")
        return IntegrationItemResponse(
            id=item.id,
            provider_type=item.provider_type,
            status=item.status,
            auth_method=item.auth_method,
            role_arn_masked=cls._mask_role_arn(role_arn),
            regions=cfg.get("regions", ["us-east-1"]),
            account_name=cfg.get("account_name"),
            last_sync_at=item.last_sync_at,
            created_at=item.created_at,
        )

    @classmethod
    async def list_integrations(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
    ) -> List[IntegrationItemResponse]:
        """Lists all configured integrations for the tenant organization."""
        res = await session.execute(
            select(Integration)
            .where(Integration.org_id == tenant.org_id)
            .order_by(desc(Integration.created_at))
        )
        return [cls._to_sanitized_response(i) for i in res.scalars().all()]

    @classmethod
    async def get_integration(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        integration_id: str,
    ) -> Optional[IntegrationItemResponse]:
        """Retrieves single integration by ID."""
        res = await session.execute(
            select(Integration).where(
                Integration.id == integration_id,
                Integration.org_id == tenant.org_id,
            )
        )
        item = res.scalars().first()
        return cls._to_sanitized_response(item) if item else None

    @classmethod
    async def configure_aws(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        req: AWSConfigureRequest,
    ) -> IntegrationItemResponse:
        """
        Creates or updates AWS integration configuration.
        Stores IAM role ARN, external ID, and regions in config_json.
        """
        res = await session.execute(
            select(Integration).where(
                Integration.org_id == tenant.org_id,
                Integration.provider_type == "AWS",
            )
        )
        integration = res.scalars().first()

        config_data = {
            "role_arn": req.role_arn,
            "external_id": req.external_id,
            "regions": req.regions,
            "account_name": req.account_name,
        }

        if integration:
            integration.config_json = config_data
            integration.status = "CONFIGURED"
        else:
            integration = Integration(
                org_id=tenant.org_id,
                provider_type="AWS",
                status="CONFIGURED",
                auth_method="IAM_ROLE",
                config_json=config_data,
            )
            session.add(integration)

        await session.commit()
        await session.refresh(integration)
        return cls._to_sanitized_response(integration)

    @classmethod
    async def validate_aws(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        req: AWSValidateRequest,
    ) -> AWSValidationResponse:
        """
        Validates connection via STS AssumeRole and bounded permission probe.
        Can validate an unsaved candidate configuration or an existing integration.
        """
        role_arn = req.role_arn
        external_id = req.external_id
        region = req.region or "us-east-1"

        if not role_arn:
            # Look up saved integration
            res = await session.execute(
                select(Integration).where(
                    Integration.org_id == tenant.org_id,
                    Integration.provider_type == "AWS",
                )
            )
            item = res.scalars().first()
            if item and item.config_json:
                role_arn = item.config_json.get("role_arn")
                external_id = item.config_json.get("external_id")
                region = item.config_json.get("region") or region

        if not role_arn:
            return AWSValidationResponse(
                is_valid=False,
                permissions=AWSServicePermissions(),
                error_message="No AWS IAM Role ARN provided or configured.",
            )

        factory = AWSClientFactory(
            role_arn=role_arn,
            external_id=external_id,
            region_name=region,
        )

        val_result = AWSAuthenticator.validate_connection(factory)
        return AWSValidationResponse(
            is_valid=val_result.is_valid,
            account_id=val_result.account_id,
            region=val_result.region,
            role_arn_masked=val_result.role_arn_masked,
            permissions=val_result.permissions,
            error_message=val_result.error_message,
        )

    @classmethod
    async def trigger_sync(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        integration_id: str,
        client_factory: Optional[AWSClientFactory] = None,
    ) -> SyncTriggerResponse:
        """Triggers a read-only synchronization pass."""
        result = await SyncCoordinator.execute_sync(
            session=session,
            integration_id=integration_id,
            org_id=tenant.org_id,
            client_factory=client_factory,
        )
        return SyncTriggerResponse(**result)

    @classmethod
    async def list_sync_jobs(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        integration_id: str,
        limit: int = 20,
    ) -> List[SyncJobItemResponse]:
        """Lists recent sync jobs for an integration."""
        res = await session.execute(
            select(SyncJob)
            .join(Integration, SyncJob.integration_id == Integration.id)
            .where(
                SyncJob.integration_id == integration_id,
                Integration.org_id == tenant.org_id,
            )
            .order_by(desc(SyncJob.started_at))
            .limit(limit)
        )
        return [
            SyncJobItemResponse(
                id=j.id,
                integration_id=j.integration_id,
                account_id=j.account_id,
                job_type=j.job_type,
                status=j.status,
                started_at=j.started_at,
                completed_at=j.completed_at,
                records_synced=j.records_synced,
                error_message=j.error_message,
            )
            for j in res.scalars().all()
        ]

    @classmethod
    async def get_status(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        integration_id: str,
    ) -> Optional[IntegrationStatusResponse]:
        """Computes comprehensive health, freshness, and capability status."""
        int_res = await session.execute(
            select(Integration).where(
                Integration.id == integration_id,
                Integration.org_id == tenant.org_id,
            )
        )
        item = int_res.scalars().first()
        if not item:
            return None

        # Fetch latest sync job
        job_res = await session.execute(
            select(SyncJob)
            .where(SyncJob.integration_id == integration_id)
            .order_by(desc(SyncJob.started_at))
            .limit(1)
        )
        latest_job = job_res.scalars().first()

        # Compute freshness
        is_fresh = False
        freshness_desc = "Never synchronized"
        now = datetime.now(timezone.utc)
        if item.last_sync_at:
            delta = now - item.last_sync_at
            if delta < timedelta(hours=24):
                is_fresh = True
                freshness_desc = f"Synchronized {int(delta.total_seconds() // 3600)}h ago"
            else:
                freshness_desc = f"Stale: last sync {delta.days}d ago"

        # Probe permissions lightweight
        cfg = item.config_json or {}
        factory = AWSClientFactory(
            role_arn=cfg.get("role_arn"),
            external_id=cfg.get("external_id"),
            region_name=cfg.get("region") or "us-east-1",
        )
        val = AWSAuthenticator.validate_connection(factory)

        return IntegrationStatusResponse(
            integration=cls._to_sanitized_response(item),
            permissions=val.permissions,
            last_sync_job=(
                SyncJobItemResponse(
                    id=latest_job.id,
                    integration_id=latest_job.integration_id,
                    account_id=latest_job.account_id,
                    job_type=latest_job.job_type,
                    status=latest_job.status,
                    started_at=latest_job.started_at,
                    completed_at=latest_job.completed_at,
                    records_synced=latest_job.records_synced,
                    error_message=latest_job.error_message,
                )
                if latest_job
                else None
            ),
            is_fresh=is_fresh,
            freshness_description=freshness_desc,
        )
