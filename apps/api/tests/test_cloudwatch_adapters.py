"""
NEXORA ATLAS - CloudWatch Adapter & Query Planner Tests
Verifies that:
1. Query planner batches MetricDataQueries up to 500 per request.
2. Adapter paginates NextToken safely up to MAX_PAGES_PER_QUERY.
3. AccessDeniedException degrades gracefully without crashing ingestion.
"""

from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError
import pytest

from app.integrations.providers.aws.client import AWSClientFactory
from app.integrations.providers.aws.telemetry.queries import TelemetryQueryPlanner
from app.integrations.providers.aws.telemetry.client import AWSTelemetryAdapter, TelemetryExecutionReport


class MockResource:
    def __init__(self, native_id, resource_type, region_code="us-east-1"):
        self.id = f"uuid-{native_id}"
        self.native_id = native_id
        self.resource_type = resource_type
        self.region_code = region_code


def test_query_planner_batching_and_limits():
    """Verifies that 120 resources producing > 500 queries are split into multiple batches."""
    # 120 EC2 instances * 5 metrics = 600 queries -> should split into 2 batches
    resources = [MockResource(f"i-{i:04d}", "INSTANCE") for i in range(120)]
    now = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
    start = now - timedelta(days=14)

    plan = TelemetryQueryPlanner.plan_queries(
        resources=resources,
        start_time=start,
        end_time=now,
    )

    assert plan.resources_planned_count == 120
    assert plan.total_queries == 120 * 5  # 5 metrics per EC2
    assert len(plan.batches) == 2
    assert plan.batches[0].metric_data_query_count == 500
    assert plan.batches[1].metric_data_query_count == 100


def test_telemetry_adapter_pagination_with_next_token():
    """Verifies that adapter loops over NextToken and accumulates data points."""
    mock_factory = MagicMock(spec=AWSClientFactory)
    mock_cw = MagicMock()

    now = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
    # Page 1 returns NextToken
    page1 = {
        "MetricDataResults": [
            {"Id": "q_cpu_1", "Timestamps": [now], "Values": [10.0]}
        ],
        "NextToken": "tok-page-2",
    }
    # Page 2 finishes
    page2 = {
        "MetricDataResults": [
            {"Id": "q_cpu_1", "Timestamps": [now + timedelta(hours=1)], "Values": [15.0]}
        ]
    }
    mock_cw.get_metric_data.side_effect = [page1, page2]
    mock_factory.get_client.return_value = mock_cw

    adapter = AWSTelemetryAdapter(mock_factory)
    res = MockResource("i-001", "INSTANCE")
    plan = TelemetryQueryPlanner.plan_queries([res], now - timedelta(days=1), now)

    report = TelemetryExecutionReport()
    results = adapter.execute_batch(plan.batches[0], now - timedelta(days=1), now, report=report)

    assert len(results) == 2
    assert report.pages_fetched == 2
    assert report.data_points_received == 2
    assert mock_cw.get_metric_data.call_count == 2


def test_telemetry_adapter_graceful_access_denied_degradation():
    """Verifies that 403 AccessDenied does not raise an unhandled exception."""
    mock_factory = MagicMock(spec=AWSClientFactory)
    mock_cw = MagicMock()

    err_response = {"Error": {"Code": "AccessDeniedException", "Message": "Not authorized"}}
    mock_cw.get_metric_data.side_effect = ClientError(err_response, "GetMetricData")
    mock_factory.get_client.return_value = mock_cw

    adapter = AWSTelemetryAdapter(mock_factory)
    res = MockResource("i-001", "INSTANCE")
    plan = TelemetryQueryPlanner.plan_queries([res], datetime.now(timezone.utc) - timedelta(days=1), datetime.now(timezone.utc))

    report = TelemetryExecutionReport()
    results = adapter.execute_batch(plan.batches[0], datetime.now(timezone.utc) - timedelta(days=1), datetime.now(timezone.utc), report=report)

    assert results == []
    assert len(report.access_denied_regions) == 1
    assert "CloudWatch_us-east-1" in report.errors
