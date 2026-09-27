"""
NEXORA ATLAS - AWS CloudWatch Telemetry Adapter
Executes planned GetMetricData batches with bounded pagination, hard ceilings,
retry on transient throttling, and graceful degradation on permission denials.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from botocore.exceptions import ClientError

from app.integrations.providers.aws.client import AWSClientFactory
from app.integrations.providers.aws.telemetry.constants import (
    MAX_PAGES_PER_QUERY,
    MAX_DATA_POINTS_PER_SYNC,
)
from app.integrations.providers.aws.telemetry.queries import TelemetryQueryBatch, PlannedQueryMetadata

logger = logging.getLogger("atlas.aws.telemetry")


class TelemetryExecutionReport:
    """Summary of CloudWatch API consumption and data point yield."""
    def __init__(self):
        self.queries_requested: int = 0
        self.queries_executed: int = 0
        self.data_points_received: int = 0
        self.pages_fetched: int = 0
        self.access_denied_regions: List[str] = []
        self.errors: Dict[str, str] = {}


class AWSTelemetryAdapter:
    """Read-only CloudWatch adapter for operational telemetry."""

    def __init__(self, client_factory: AWSClientFactory):
        self.client_factory = client_factory

    def execute_batch(
        self,
        batch: TelemetryQueryBatch,
        start_time: datetime,
        end_time: datetime,
        report: Optional[TelemetryExecutionReport] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes a single regional batch of MetricDataQueries.
        Paginates NextToken up to MAX_PAGES_PER_QUERY.
        Returns raw MetricDataResult list.
        """
        if not batch.metric_data_queries:
            return []

        if report:
            report.queries_requested += batch.metric_data_query_count

        results: List[Dict[str, Any]] = []
        region = batch.region_code
        cw_client = self.client_factory.get_client("cloudwatch", region=region)

        next_token: Optional[str] = None
        pages_count = 0
        total_points = 0

        while True:
            if pages_count >= MAX_PAGES_PER_QUERY:
                logger.warning(
                    "CloudWatch query reached MAX_PAGES_PER_QUERY (%d) in region %s",
                    MAX_PAGES_PER_QUERY,
                    region,
                )
                break

            kwargs: Dict[str, Any] = {
                "MetricDataQueries": batch.metric_data_queries,
                "StartTime": start_time,
                "EndTime": end_time,
                "ScanBy": "TimestampAscending",
            }
            if next_token:
                kwargs["NextToken"] = next_token

            def _call():
                return cw_client.get_metric_data(**kwargs)

            try:
                response = AWSClientFactory.execute_with_retry("GetMetricData", _call)
            except (ClientError, Exception) as e:
                err_str = str(e)
                code = ""
                if isinstance(e, ClientError):
                    code = e.response.get("Error", {}).get("Code", "")
                logger.warning("GetMetricData failed in %s: %s", region, err_str)
                if "AccessDenied" in code or "AccessDenied" in err_str or "Not authorized" in err_str:
                    if report:
                        report.access_denied_regions.append(region)
                        report.errors[f"CloudWatch_{region}"] = "AccessDenied to cloudwatch:GetMetricData"
                else:
                    if report:
                        report.errors[f"CloudWatch_{region}"] = err_str
                break

            pages_count += 1
            page_results = response.get("MetricDataResults", [])
            page_pts = 0
            for res in page_results:
                pts_len = len(res.get("Values", []))
                page_pts += pts_len
                results.append(res)

            total_points += page_pts
            if report:
                report.queries_executed += batch.metric_data_query_count
                report.pages_fetched += 1
                report.data_points_received += page_pts

            next_token = response.get("NextToken")
            if not next_token or total_points >= MAX_DATA_POINTS_PER_SYNC:
                break

        return results
