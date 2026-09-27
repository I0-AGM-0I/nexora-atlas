"""
NEXORA ATLAS - Operational Telemetry Service Layer
Coordinates querying, statistical rollups, data quality reporting, and on-demand synchronization.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, func, distinct, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import CloudAccount, Integration
from app.models.resource import CloudResource
from app.models.telemetry import ResourceMetricObservation
from app.services.tenant import TenantContext
from app.integrations.providers.aws.telemetry.processor import TelemetryStatisticalProcessor
from app.schemas.telemetry import (
    ResourceTelemetryResponse,
    TelemetryMetricSummary,
    TelemetryObservationItem,
    IntegrationTelemetryStatusResponse,
    DataQualityReportResponse,
    AccountDataQualityItem,
)
from app.schemas.integrations import SyncTriggerResponse
from app.integrations.sync.coordinator import SyncCoordinator


class TelemetryService:
    """Service layer managing operational telemetry and data trustworthiness reports."""

    @classmethod
    async def get_resource_telemetry(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        resource_id: str,
        days: int = 30,
    ) -> ResourceTelemetryResponse:
        """Retrieves operational telemetry time-series and computed statistical rollups for a resource."""
        # 1. Verify resource exists and belongs to tenant accounts
        res_stmt = select(CloudResource).where(
            CloudResource.id == resource_id,
            CloudResource.account_id.in_(tenant.account_ids),
        )
        res_result = await session.execute(res_stmt)
        resource = res_result.scalar_one_or_none()
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource '{resource_id}' not found.",
            )

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(days=days)

        # 2. Query all observations within the requested window
        obs_stmt = (
            select(ResourceMetricObservation)
            .where(
                ResourceMetricObservation.resource_id == resource_id,
                ResourceMetricObservation.timestamp >= window_start,
            )
            .order_by(ResourceMetricObservation.timestamp.desc())
        )
        obs_result = await session.execute(obs_stmt)
        observations = obs_result.scalars().all()

        # 3. Group by metric name and process statistical rollups
        grouped_obs: Dict[str, List[ResourceMetricObservation]] = {}
        for o in observations:
            grouped_obs.setdefault(o.metric_name, []).append(o)

        metrics_summary: Dict[str, TelemetryMetricSummary] = {}
        for metric_name, obs_list in grouped_obs.items():
            first_obs = obs_list[0]
            unit = first_obs.unit or ""
            period = first_obs.period or 300
            is_activity = "bytes" in metric_name.lower() or "ops" in metric_name.lower() or "requests" in metric_name.lower()

            stats = TelemetryStatisticalProcessor.process_series(
                metric_name=metric_name,
                unit=unit,
                observations=obs_list,
                window_start=window_start,
                window_end=now,
                period_seconds=period,
                now=now,
                is_activity_metric=is_activity,
            )

            metrics_summary[metric_name] = TelemetryMetricSummary(
                metric_name=metric_name,
                namespace=first_obs.namespace,
                unit=unit,
                source_statistic=first_obs.source_statistic,
                observation_count=stats.sample_count,
                p95=stats.p95,
                median=stats.median,
                mean=stats.mean,
                min_value=stats.minimum,
                max_value=stats.maximum,
                latest_value=stats.median if stats.latest_timestamp else None,
                latest_timestamp=stats.latest_timestamp,
                coverage_ratio=stats.coverage_ratio,
                freshness_age_seconds=stats.freshness_age_seconds,
                sufficiency_status=stats.sufficiency_status.value,
            )

        # 4. Take the most recent 100 observations for plotting
        recent = [
            TelemetryObservationItem(
                id=o.id,
                timestamp=o.timestamp,
                metric_name=o.metric_name,
                namespace=o.namespace,
                source_statistic=o.source_statistic,
                value=o.value,
                unit=o.unit,
                period=o.period,
                dimensions_json=o.dimensions_json or {},
            )
            for o in observations[:100]
        ]

        return ResourceTelemetryResponse(
            resource_id=resource.id,
            resource_name=resource.name,
            native_id=resource.native_id,
            service_name=resource.service_name,
            resource_type=resource.resource_type,
            window_days=days,
            metrics=metrics_summary,
            recent_observations=recent,
        )

    @classmethod
    async def get_integration_telemetry_status(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        integration_id: str,
    ) -> IntegrationTelemetryStatusResponse:
        """Evaluates operational telemetry coverage and permissions for an integration or account."""
        integ_res = await session.execute(
            select(Integration).where(
                Integration.id == integration_id,
                Integration.org_id == tenant.org_id,
            )
        )
        integration = integ_res.scalars().first()

        # Resolve target account ID
        target_account_id = integration_id
        if integration and integration.config_json:
            target_account_id = integration.config_json.get("account_id", integration_id)

        # Total resources
        total_res_stmt = select(func.count(CloudResource.id)).where(
            CloudResource.account_id.in_(tenant.account_ids),
        )
        total_resources = (await session.execute(total_res_stmt)).scalar() or 0

        # Resources with telemetry
        telemetry_res_stmt = select(
            func.count(distinct(ResourceMetricObservation.resource_id))
        ).where(
            ResourceMetricObservation.organization_id == tenant.org_id,
        )
        resources_with_telemetry = (await session.execute(telemetry_res_stmt)).scalar() or 0

        overall_cov = Decimal("0.00")
        if total_resources > 0:
            overall_cov = (
                (Decimal(str(resources_with_telemetry)) / Decimal(str(total_resources)))
                * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Latest observation timestamp
        latest_ts_stmt = select(func.max(ResourceMetricObservation.timestamp)).where(
            ResourceMetricObservation.organization_id == tenant.org_id,
        )
        last_sync = (await session.execute(latest_ts_stmt)).scalar()

        # Check permissions status
        cw_permission = "GRANTED"
        if integration and integration.config_json:
            cw_permission = "GRANTED" if integration.config_json.get("permissions", {}).get("cloudwatch_telemetry", True) else "DENIED"

        return IntegrationTelemetryStatusResponse(
            integration_id=integration_id,
            cloudwatch_permission_status=cw_permission,
            telemetry_enabled=cw_permission == "GRANTED",
            total_resources_tracked=total_resources,
            resources_with_telemetry=resources_with_telemetry,
            overall_coverage_pct=overall_cov,
            last_telemetry_sync=last_sync,
            supported_namespaces=[
                "AWS/EC2",
                "AWS/RDS",
                "AWS/EBS",
                "AWS/S3",
                "ContainerInsights",
            ],
        )

    @classmethod
    async def trigger_telemetry_sync(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        integration_id: str,
    ) -> SyncTriggerResponse:
        """Triggers an on-demand operational telemetry synchronization."""
        result = await SyncCoordinator.execute_sync(
            session=session,
            integration_id=integration_id,
            org_id=tenant.org_id,
        )
        return SyncTriggerResponse(**result)

    @classmethod
    async def get_data_quality_report(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
    ) -> DataQualityReportResponse:
        """Builds a deterministic data quality and telemetry trustworthiness report."""
        # 1. Accounts
        acc_stmt = select(CloudAccount).where(CloudAccount.org_id == tenant.org_id)
        accounts = (await session.execute(acc_stmt)).scalars().all()
        total_accounts = len(accounts)

        # 2. Total resources
        if tenant.account_ids:
            res_stmt = select(CloudResource).where(CloudResource.account_id.in_(tenant.account_ids))
            all_resources = (await session.execute(res_stmt)).scalars().all()
        else:
            all_resources = []
        total_resources = len(all_resources)

        # 3. Telemetry metrics breakdown
        metrics_stmt = (
            select(
                ResourceMetricObservation.metric_name,
                func.count(ResourceMetricObservation.id),
            )
            .where(ResourceMetricObservation.organization_id == tenant.org_id)
            .group_by(ResourceMetricObservation.metric_name)
        )
        metrics_rows = (await session.execute(metrics_stmt)).all()
        metrics_breakdown = {name: count for name, count in metrics_rows}
        total_observations = sum(metrics_breakdown.values())

        # 4. Distinct resources with telemetry
        distinct_res_stmt = select(
            func.count(distinct(ResourceMetricObservation.resource_id))
        ).where(ResourceMetricObservation.organization_id == tenant.org_id)
        resources_with_telemetry = (await session.execute(distinct_res_stmt)).scalar() or 0

        telemetry_coverage_pct = Decimal("0.00")
        if total_resources > 0:
            telemetry_coverage_pct = (
                (Decimal(str(resources_with_telemetry)) / Decimal(str(total_resources)))
                * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 5. Accounts breakdown
        accounts_quality: List[AccountDataQualityItem] = []
        for acc in accounts:
            acc_res_count = sum(1 for r in all_resources if r.account_id == acc.id)
            acc_distinct_stmt = select(
                func.count(distinct(ResourceMetricObservation.resource_id))
            ).where(
                ResourceMetricObservation.cloud_account_id == acc.id,
                ResourceMetricObservation.organization_id == tenant.org_id,
            )
            acc_telemetry_res = (await session.execute(acc_distinct_stmt)).scalar() or 0

            acc_obs_stmt = select(func.count(ResourceMetricObservation.id)).where(
                ResourceMetricObservation.cloud_account_id == acc.id,
                ResourceMetricObservation.organization_id == tenant.org_id,
            )
            acc_obs_count = (await session.execute(acc_obs_stmt)).scalar() or 0

            acc_cov = Decimal("0.00")
            if acc_res_count > 0:
                acc_cov = (
                    (Decimal(str(acc_telemetry_res)) / Decimal(str(acc_res_count)))
                    * Decimal("100")
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            accounts_quality.append(
                AccountDataQualityItem(
                    account_id=acc.id,
                    account_name=acc.name,
                    total_resources=acc_res_count,
                    resources_with_telemetry=acc_telemetry_res,
                    telemetry_coverage_pct=acc_cov,
                    total_observations=acc_obs_count,
                )
            )

        # Trustworthiness status
        if telemetry_coverage_pct >= Decimal("70.00"):
            trust_status = "TRUSTED"
        elif telemetry_coverage_pct > Decimal("0.00"):
            trust_status = "LIMITED_TELEMETRY"
        else:
            trust_status = "NO_OPERATIONAL_DATA"

        return DataQualityReportResponse(
            organization_id=tenant.org_id,
            generated_at=datetime.now(timezone.utc),
            total_accounts=total_accounts,
            total_resources=total_resources,
            resources_with_telemetry=resources_with_telemetry,
            telemetry_coverage_pct=telemetry_coverage_pct,
            total_observations=total_observations,
            accounts_quality=accounts_quality,
            metrics_breakdown=metrics_breakdown,
            data_trustworthiness_status=trust_status,
        )
