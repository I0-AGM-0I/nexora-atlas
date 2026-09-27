"""
NEXORA ATLAS - CloudWatch Telemetry Query Planner
Batches metric retrieval into bounded GetMetricData requests.
Respects AWS 500 MetricDataQuery limits, tracks estimated data points,
and groups queries regionally to avoid cross-region latency.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field

from app.integrations.providers.aws.telemetry.constants import (
    MAX_METRIC_DATA_QUERIES_PER_REQUEST,
    MAX_RESOURCES_PER_TELEMETRY_SYNC,
    DEFAULT_METRIC_PERIOD_SECONDS,
)
from app.integrations.providers.aws.telemetry.catalog import MetricCatalog, MetricDefinition


class PlannedQueryMetadata(BaseModel):
    """Metadata mapping a query ID back to the canonical resource and metric."""
    query_id: str
    resource_id: str
    native_id: str
    region_code: str
    metric_namespace: str
    metric_name: str
    source_statistic: str
    period_seconds: int
    unit: str
    dimensions: Dict[str, str]


class TelemetryQueryBatch(BaseModel):
    """A bounded batch of MetricDataQueries destined for a single AWS region."""
    region_code: str
    metric_data_queries: List[Dict[str, Any]]
    metadata_by_query_id: Dict[str, PlannedQueryMetadata]
    metric_data_query_count: int
    estimated_data_points: int


class TelemetryPlan(BaseModel):
    """Overall execution plan across all target regions."""
    batches: List[TelemetryQueryBatch]
    total_queries: int
    total_estimated_data_points: int
    resources_planned_count: int


class TelemetryQueryPlanner:
    """Plans bounded, deterministic GetMetricData batches."""

    @classmethod
    def plan_queries(
        cls,
        resources: List[Any],  # CloudResource or DiscoveredResource
        start_time: datetime,
        end_time: datetime,
        custom_definitions: Optional[List[MetricDefinition]] = None,
        period_seconds: int = DEFAULT_METRIC_PERIOD_SECONDS,
        default_region: str = "us-east-1",
    ) -> TelemetryPlan:
        """
        Creates bounded batches of GetMetricData queries partitioned by AWS region.
        Enforces MAX_RESOURCES_PER_TELEMETRY_SYNC and MAX_METRIC_DATA_QUERIES_PER_REQUEST.
        """
        capped_resources = resources[:MAX_RESOURCES_PER_TELEMETRY_SYNC]
        window_seconds = max(1, int((end_time - start_time).total_seconds()))
        expected_points_per_metric = max(1, window_seconds // period_seconds)

        # Group resources by region
        queries_by_region: Dict[str, List[Tuple[Dict[str, Any], PlannedQueryMetadata]]] = {}

        for res in capped_resources:
            res_id = getattr(res, "id", None) or getattr(res, "native_id", "")
            native_id = getattr(res, "native_id", "")
            res_type = getattr(res, "resource_type", "")
            region = getattr(res, "region_code", None) or getattr(res, "region", None) or default_region
            # If resource is DB model with region relationship:
            if hasattr(res, "region") and res.region and hasattr(res.region, "region_code"):
                region = res.region.region_code

            dim_name = MetricCatalog.get_dimension_name_for_resource(res_type)
            if not dim_name or not native_id:
                continue

            definitions = custom_definitions or MetricCatalog.get_definitions_for_resource(res_type)
            for defn in definitions:
                # S3 bucket metrics use daily periods (86400)
                actual_period = defn.default_period_seconds
                stat = defn.source_statistics[0] if defn.source_statistics else "Average"

                # Unique alphanumeric query ID conforming to CloudWatch syntax [a-z][a-zA-Z0-9_]*
                clean_native = "".join(c for c in native_id if c.isalnum())[-12:]
                clean_metric = "".join(c for c in defn.metric_name if c.isalnum())[-12:]
                q_id = f"q_{clean_metric}_{clean_native}_{len(queries_by_region.get(region, []))}"

                dimensions = [{"Name": dim_name, "Value": native_id}]
                dims_map = {dim_name: native_id}
                if defn.namespace == "AWS/S3":
                    dimensions.append({"Name": "StorageType", "Value": "StandardStorage"})
                    dims_map["StorageType"] = "StandardStorage"

                cw_query = {
                    "Id": q_id,
                    "MetricStat": {
                        "Metric": {
                            "Namespace": defn.namespace,
                            "MetricName": defn.metric_name,
                            "Dimensions": dimensions,
                        },
                        "Period": actual_period,
                        "Stat": stat,
                        "Unit": defn.unit,
                    },
                    "ReturnData": True,
                }

                meta = PlannedQueryMetadata(
                    query_id=q_id,
                    resource_id=res_id,
                    native_id=native_id,
                    region_code=region,
                    metric_namespace=defn.namespace,
                    metric_name=defn.metric_name,
                    source_statistic=stat,
                    period_seconds=actual_period,
                    unit=defn.unit,
                    dimensions=dims_map,
                )

                queries_by_region.setdefault(region, []).append((cw_query, meta))

        # Chunk into bounded batches per region
        batches: List[TelemetryQueryBatch] = []
        total_queries = 0
        total_points = 0

        for region, q_list in queries_by_region.items():
            for i in range(0, len(q_list), MAX_METRIC_DATA_QUERIES_PER_REQUEST):
                chunk = q_list[i : i + MAX_METRIC_DATA_QUERIES_PER_REQUEST]
                batch_queries = [item[0] for item in chunk]
                batch_meta = {item[1].query_id: item[1] for item in chunk}
                est_points = len(chunk) * expected_points_per_metric

                batches.append(
                    TelemetryQueryBatch(
                        region_code=region,
                        metric_data_queries=batch_queries,
                        metadata_by_query_id=batch_meta,
                        metric_data_query_count=len(batch_queries),
                        estimated_data_points=est_points,
                    )
                )
                total_queries += len(batch_queries)
                total_points += est_points

        return TelemetryPlan(
            batches=batches,
            total_queries=total_queries,
            total_estimated_data_points=total_points,
            resources_planned_count=len(capped_resources),
        )
