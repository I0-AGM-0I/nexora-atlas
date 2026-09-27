"""
NEXORA ATLAS - Telemetry Normalization & Model Mapper
Converts raw CloudWatch MetricDataResult objects into canonical ResourceMetricObservation models.
Enforces deterministic SHA-256 source observation keys and exact 4-decimal arithmetic.
"""

import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.models.telemetry import ResourceMetricObservation
from app.integrations.providers.aws.telemetry.queries import PlannedQueryMetadata


class TelemetryModelMapper:
    """Normalizes CloudWatch metric data points into canonical entities."""

    @staticmethod
    def generate_source_observation_key(
        provider_type: str,
        account_id: str,
        region_code: str,
        metric_namespace: str,
        metric_name: str,
        dimensions: Dict[str, Any],
        timestamp: datetime,
        period_seconds: int,
        source_statistic: str,
    ) -> str:
        """
        Builds deterministic cryptographic digest for an operational observation.
        Includes provider, account, region, namespace, metric, sorted dimensions,
        ISO timestamp, period, and source statistic.
        """
        dims_str = json.dumps(dimensions, sort_keys=True)
        ts_iso = timestamp.isoformat()
        digest_input = (
            f"{provider_type}|{account_id}|{region_code}|{metric_namespace}|"
            f"{metric_name}|{dims_str}|{ts_iso}|{period_seconds}|{source_statistic}"
        )
        return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()

    @classmethod
    def map_metric_data_results(
        cls,
        metric_results: List[Dict[str, Any]],
        metadata_by_query_id: Dict[str, PlannedQueryMetadata],
        org_id: str,
        cloud_account_id: str,
        account_id_native: str,
        sync_job_id: Optional[str] = None,
        retrieved_at: Optional[datetime] = None,
        resource_id_map: Optional[Dict[str, str]] = None,  # (region, native_id) -> db_resource_id
    ) -> List[ResourceMetricObservation]:
        """
        Transforms raw MetricDataResult list into canonical ResourceMetricObservation rows.
        """
        now = retrieved_at or datetime.now(timezone.utc)
        observations: List[ResourceMetricObservation] = []

        for res in metric_results:
            q_id = res.get("Id")
            meta = metadata_by_query_id.get(q_id)
            if not meta:
                continue

            timestamps = res.get("Timestamps", [])
            values = res.get("Values", [])
            if len(timestamps) != len(values):
                continue

            # Resolve canonical resource_id using provider + account + region + native_id
            resolved_resource_id = meta.resource_id
            if resource_id_map:
                key = (meta.region_code, meta.native_id)
                if key in resource_id_map:
                    resolved_resource_id = resource_id_map[key]

            for ts, val in zip(timestamps, values):
                try:
                    # Convert to exact Decimal
                    dec_val = Decimal(str(val)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                except Exception:
                    continue

                obs_key = cls.generate_source_observation_key(
                    provider_type="AWS",
                    account_id=account_id_native,
                    region_code=meta.region_code,
                    metric_namespace=meta.metric_namespace,
                    metric_name=meta.metric_name,
                    dimensions=meta.dimensions,
                    timestamp=ts,
                    period_seconds=meta.period_seconds,
                    source_statistic=meta.source_statistic,
                )

                obs = ResourceMetricObservation(
                    organization_id=org_id,
                    cloud_account_id=cloud_account_id,
                    resource_id=resolved_resource_id,
                    source_observation_key=obs_key,
                    provider_type="AWS",
                    metric_namespace=meta.metric_namespace,
                    metric_name=meta.metric_name,
                    source_statistic=meta.source_statistic,
                    period_seconds=meta.period_seconds,
                    timestamp=ts,
                    value=dec_val,
                    unit=meta.unit,
                    dimensions_json=meta.dimensions,
                    source="cloudwatch",
                    retrieved_at=now,
                    sync_job_id=sync_job_id,
                )
                observations.append(obs)

        return observations
