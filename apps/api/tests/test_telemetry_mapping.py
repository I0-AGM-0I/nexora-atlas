"""
NEXORA ATLAS - Telemetry Mapping & Identity Tests
Verifies that:
1. Telemetry observations generate deterministic cryptographic source keys.
2. Source statistics are preserved as source stats (never derived p95).
3. Resource correlation correctly resolves canonical CloudResource identity.
"""

from decimal import Decimal
from datetime import datetime, timezone
import pytest

from app.integrations.providers.aws.telemetry.mapper import TelemetryModelMapper
from app.integrations.providers.aws.telemetry.queries import PlannedQueryMetadata


def test_deterministic_source_observation_key():
    """Verifies that source observation key is repeatable and sensitive to all parameters."""
    ts = datetime(2026, 9, 18, 10, 0, 0, tzinfo=timezone.utc)
    dims = {"InstanceId": "i-0123456789abcdef0"}

    key1 = TelemetryModelMapper.generate_source_observation_key(
        provider_type="AWS",
        account_id="123456789012",
        region_code="us-east-1",
        metric_namespace="AWS/EC2",
        metric_name="CPUUtilization",
        dimensions=dims,
        timestamp=ts,
        period_seconds=3600,
        source_statistic="Average",
    )

    key2 = TelemetryModelMapper.generate_source_observation_key(
        provider_type="AWS",
        account_id="123456789012",
        region_code="us-east-1",
        metric_namespace="AWS/EC2",
        metric_name="CPUUtilization",
        dimensions=dims,
        timestamp=ts,
        period_seconds=3600,
        source_statistic="Average",
    )

    # Determinism
    assert key1 == key2
    assert len(key1) == 64

    # Sensitivity to statistic
    key_max = TelemetryModelMapper.generate_source_observation_key(
        provider_type="AWS",
        account_id="123456789012",
        region_code="us-east-1",
        metric_namespace="AWS/EC2",
        metric_name="CPUUtilization",
        dimensions=dims,
        timestamp=ts,
        period_seconds=3600,
        source_statistic="Maximum",
    )
    assert key1 != key_max


def test_mapping_metric_data_results_preserves_source_statistic():
    """Verifies that source statistic is preserved and raw observations are correctly created."""
    ts = datetime(2026, 9, 18, 10, 0, 0, tzinfo=timezone.utc)
    meta = PlannedQueryMetadata(
        query_id="q_cpu_i123_0",
        resource_id="res-placeholder",
        native_id="i-0123456789abcdef0",
        region_code="us-east-1",
        metric_namespace="AWS/EC2",
        metric_name="CPUUtilization",
        source_statistic="Average",
        period_seconds=3600,
        unit="Percent",
        dimensions={"InstanceId": "i-0123456789abcdef0"},
    )

    raw_results = [
        {
            "Id": "q_cpu_i123_0",
            "Timestamps": [ts],
            "Values": [12.45678],
            "StatusCode": "Complete",
        }
    ]

    res_map = {("us-east-1", "i-0123456789abcdef0"): "res-canonical-uuid-999"}

    obs = TelemetryModelMapper.map_metric_data_results(
        metric_results=raw_results,
        metadata_by_query_id={"q_cpu_i123_0": meta},
        org_id="org-test-uuid",
        cloud_account_id="acc-test-uuid",
        account_id_native="123456789012",
        resource_id_map=res_map,
    )

    assert len(obs) == 1
    item = obs[0]
    assert item.resource_id == "res-canonical-uuid-999"
    assert item.metric_name == "CPUUtilization"
    assert item.source_statistic == "Average"  # Strictly source statistic, NOT p95
    assert item.value == Decimal("12.4568")  # Quantized to 4 decimal places
    assert item.unit == "Percent"
    assert item.source_observation_key is not None
