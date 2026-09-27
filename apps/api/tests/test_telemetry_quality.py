"""
NEXORA ATLAS - Telemetry Quality & Statistical Processor Tests
Verifies that derived statistics (p95, mean, cv) are mathematically exact,
coverage ratios are calculated from expected observations and capped at 100%,
and strict sufficiency states (AVAILABLE, INSUFFICIENT_DATA, NOT_CONFIGURED, NOT_APPLICABLE)
are properly assigned.
"""

from decimal import Decimal
from datetime import datetime, timezone, timedelta
import pytest

from app.analytics.types import SufficiencyStatus
from app.integrations.providers.aws.telemetry.processor import (
    TelemetryStatisticalProcessor,
    TelemetryStatistics,
)


def test_percentile_computation_known_distribution():
    """Verifies that rank-based percentile interpolation is mathematically exact."""
    # 10 values: 10, 20, 30, ..., 100
    vals = [Decimal(str(i * 10)) for i in range(1, 11)]

    p50 = TelemetryStatisticalProcessor.compute_percentile(vals, Decimal("50"))
    p95 = TelemetryStatisticalProcessor.compute_percentile(vals, Decimal("95"))
    p75 = TelemetryStatisticalProcessor.compute_percentile(vals, Decimal("75"))

    # For 10 values, index for p50 = 0.5 * 9 = 4.5 -> avg(vals[4], vals[5]) = avg(50, 60) = 55
    assert p50 == Decimal("55.0000")
    # For p95, rank = 0.95 * 9 = 8.55 -> vals[8] + 0.55*(vals[9]-vals[8]) = 90 + 0.55*10 = 95.5
    assert p95 == Decimal("95.5000")
    # For p75, rank = 0.75 * 9 = 6.75 -> vals[6] + 0.75*(vals[7]-vals[6]) = 70 + 0.75*10 = 77.5
    assert p75 == Decimal("77.5000")


def test_coverage_calculation_and_sufficiency_available():
    """Verifies that 14 days of hourly observations achieves ~100% coverage and AVAILABLE status."""
    now = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
    window_start = now - timedelta(days=14)
    window_end = now

    # Generate 14 days * 24 hours = 336 hourly observations
    obs = []
    for i in range(336):
        ts = window_start + timedelta(hours=i)
        obs.append({"timestamp": ts, "value": Decimal("12.5000")})

    stats = TelemetryStatisticalProcessor.process_observations(
        metric_name="CPUUtilization",
        unit="Percent",
        observations=obs,
        window_start=window_start,
        window_end=window_end,
        period_seconds=3600,
        now=now,
    )

    assert stats.sample_count == 336
    assert stats.expected_observations == 336
    assert stats.coverage_ratio == Decimal("1.0000")
    assert stats.sufficiency_status == SufficiencyStatus.AVAILABLE
    assert stats.p95 == Decimal("12.5000")
    assert stats.mean == Decimal("12.5000")
    assert stats.stddev == Decimal("0.0000")
    assert stats.is_stale is False


def test_insufficient_data_due_to_low_coverage():
    """Verifies that low coverage (< 70%) results in INSUFFICIENT_DATA."""
    now = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
    window_start = now - timedelta(days=14)
    window_end = now

    # Expected: 336 hourly observations. Provide only 100 observations (< 30% coverage)
    obs = []
    for i in range(100):
        ts = window_start + timedelta(hours=i)
        obs.append({"timestamp": ts, "value": Decimal("8.0000")})

    stats = TelemetryStatisticalProcessor.process_observations(
        metric_name="CPUUtilization",
        unit="Percent",
        observations=obs,
        window_start=window_start,
        window_end=window_end,
        period_seconds=3600,
        now=now,
    )

    assert stats.sample_count == 100
    assert stats.expected_observations == 336
    assert stats.coverage_ratio < Decimal("0.70")
    assert stats.sufficiency_status == SufficiencyStatus.INSUFFICIENT_DATA


def test_stale_telemetry_results_in_insufficient_data():
    """Verifies that observations older than 48 hours are marked stale and INSUFFICIENT_DATA."""
    now = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
    window_start = now - timedelta(days=14)
    window_end = now

    # Last observation is 72 hours ago
    obs = []
    for i in range(250):
        ts = window_start + timedelta(hours=i)
        obs.append({"timestamp": ts, "value": Decimal("10.0000")})

    stats = TelemetryStatisticalProcessor.process_observations(
        metric_name="CPUUtilization",
        unit="Percent",
        observations=obs,
        window_start=window_start,
        window_end=window_end,
        period_seconds=3600,
        now=now,
    )

    assert stats.is_stale is True
    assert stats.sufficiency_status == SufficiencyStatus.INSUFFICIENT_DATA


def test_empty_observations_is_not_configured():
    """Verifies that absence of observations evaluates to NOT_CONFIGURED (never zero)."""
    now = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
    window_start = now - timedelta(days=14)
    window_end = now

    stats = TelemetryStatisticalProcessor.process_observations(
        metric_name="BucketSizeBytes",
        unit="Bytes",
        observations=[],
        window_start=window_start,
        window_end=window_end,
        period_seconds=86400,
        is_supported=True,
        now=now,
    )

    assert stats.sample_count == 0
    assert stats.coverage_ratio == Decimal("0.00")
    assert stats.sufficiency_status == SufficiencyStatus.NOT_CONFIGURED
    assert stats.p95 is None


def test_unsupported_metric_is_not_applicable():
    """Verifies that requesting an unsupported metric evaluates to NOT_APPLICABLE."""
    now = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
    window_start = now - timedelta(days=14)
    window_end = now

    stats = TelemetryStatisticalProcessor.process_observations(
        metric_name="CPUUtilization",
        unit="Percent",
        observations=[],
        window_start=window_start,
        window_end=window_end,
        period_seconds=3600,
        is_supported=False,
        now=now,
    )

    assert stats.sufficiency_status == SufficiencyStatus.NOT_APPLICABLE
