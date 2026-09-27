"""
NEXORA ATLAS - Telemetry Statistical Processor & Quality Engine
Calculates deterministic derived statistics (p95, median, CV), coverage ratios,
freshness metrics, and explicit sufficiency states across operational observations.
"""

import math
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.analytics.types import SufficiencyStatus
from app.integrations.providers.aws.telemetry.constants import (
    MIN_TELEMETRY_COVERAGE_FOR_RIGHTSIZING,
    MIN_TELEMETRY_SAMPLES_FOR_ANALYSIS,
    MAX_ACCEPTABLE_FRESHNESS_AGE_HOURS,
)


class TelemetryStatistics(BaseModel):
    """Derived analytical summary of a metric time-series."""
    metric_name: str
    unit: str
    sample_count: int
    expected_observations: int
    coverage_ratio: Decimal
    sufficiency_status: SufficiencyStatus

    # Statistical properties
    p95: Optional[Decimal] = None
    p75: Optional[Decimal] = None
    p50: Optional[Decimal] = None
    median: Optional[Decimal] = None
    mean: Optional[Decimal] = None
    minimum: Optional[Decimal] = None
    maximum: Optional[Decimal] = None
    stddev: Optional[Decimal] = None
    coefficient_of_variation: Optional[Decimal] = None

    # Temporal context
    window_start: datetime
    window_end: datetime
    latest_timestamp: Optional[datetime] = None
    freshness_age_seconds: Optional[int] = None
    is_stale: bool = False
    is_activity_metric: bool = False


class TelemetryStatisticalProcessor:
    """Processes raw time-series observations into auditable analytical statistics."""

    @classmethod
    def compute_percentile(cls, sorted_values: List[Decimal], percentile: Decimal) -> Decimal:
        """
        Calculates exact rank-based percentile:
        index = (percentile / 100) * (N - 1)
        Interpolates linearly between adjacent values.
        """
        if not sorted_values:
            return Decimal("0.0000")
        if len(sorted_values) == 1:
            return sorted_values[0]

        n = len(sorted_values)
        rank = (percentile / Decimal("100")) * Decimal(str(n - 1))
        low_idx = int(rank)
        high_idx = min(n - 1, low_idx + 1)
        fraction = rank - Decimal(str(low_idx))

        low_val = sorted_values[low_idx]
        high_val = sorted_values[high_idx]
        result = low_val + (fraction * (high_val - low_val))
        return result.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    @classmethod
    def process_observations(
        cls,
        metric_name: str,
        unit: str,
        observations: List[Any],  # List of ResourceMetricObservation or dicts with timestamp/value
        window_start: datetime,
        window_end: datetime,
        period_seconds: int = 3600,
        is_supported: bool = True,
        is_activity_metric: bool = False,
        now: Optional[datetime] = None,
    ) -> TelemetryStatistics:
        """
        Computes comprehensive statistics and quality metrics from raw observations.
        Adheres to: Missing data != 0.
        """
        current_time = now or datetime.now(timezone.utc)
        total_seconds = max(1, int((window_end - window_start).total_seconds()))
        expected_samples = max(1, total_seconds // period_seconds)

        if not is_supported:
            return TelemetryStatistics(
                metric_name=metric_name,
                unit=unit,
                sample_count=0,
                expected_observations=expected_samples,
                coverage_ratio=Decimal("0.00"),
                sufficiency_status=SufficiencyStatus.NOT_APPLICABLE,
                window_start=window_start,
                window_end=window_end,
                is_activity_metric=is_activity_metric,
            )

        if not observations:
            return TelemetryStatistics(
                metric_name=metric_name,
                unit=unit,
                sample_count=0,
                expected_observations=expected_samples,
                coverage_ratio=Decimal("0.00"),
                sufficiency_status=SufficiencyStatus.NOT_CONFIGURED,
                window_start=window_start,
                window_end=window_end,
                is_activity_metric=is_activity_metric,
            )

        # Extract values and timestamps
        points: List[tuple[datetime, Decimal]] = []
        for o in observations:
            ts = getattr(o, "timestamp", None) or o.get("timestamp")
            val = getattr(o, "value", None) or o.get("value")
            if ts is not None and val is not None:
                points.append((ts, Decimal(str(val))))

        if not points:
            return TelemetryStatistics(
                metric_name=metric_name,
                unit=unit,
                sample_count=0,
                expected_observations=expected_samples,
                coverage_ratio=Decimal("0.00"),
                sufficiency_status=SufficiencyStatus.NOT_CONFIGURED,
                window_start=window_start,
                window_end=window_end,
                is_activity_metric=is_activity_metric,
            )

        # Sort points by timestamp
        points.sort(key=lambda x: x[0])
        latest_ts = points[-1][0]
        freshness_age = max(0, int((current_time - latest_ts).total_seconds()))
        is_stale = freshness_age > (MAX_ACCEPTABLE_FRESHNESS_AGE_HOURS * 3600)

        values = [p[1] for p in points]
        sorted_vals = sorted(values)
        sample_count = len(values)

        # Calculate coverage ratio capped at 100%
        raw_cov = Decimal(str(sample_count)) / Decimal(str(expected_samples))
        coverage_ratio = min(Decimal("1.0000"), raw_cov).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # Evaluate sufficiency status
        if sample_count < MIN_TELEMETRY_SAMPLES_FOR_ANALYSIS or coverage_ratio < MIN_TELEMETRY_COVERAGE_FOR_RIGHTSIZING or is_stale:
            sufficiency = SufficiencyStatus.INSUFFICIENT_DATA
        else:
            sufficiency = SufficiencyStatus.AVAILABLE

        # Statistical calculations
        p95 = cls.compute_percentile(sorted_vals, Decimal("95"))
        p75 = cls.compute_percentile(sorted_vals, Decimal("75"))
        p50 = cls.compute_percentile(sorted_vals, Decimal("50"))
        median = p50
        min_val = sorted_vals[0]
        max_val = sorted_vals[-1]

        mean_val = (sum(values) / Decimal(str(sample_count))).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

        # Standard deviation and Coefficient of Variation
        variance = sum(((v - mean_val) ** 2 for v in values)) / Decimal(str(sample_count))
        stddev_val = Decimal(str(math.sqrt(float(variance)))).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        if mean_val > Decimal("0"):
            cv_val = (stddev_val / mean_val).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        else:
            cv_val = Decimal("0.0000")

        return TelemetryStatistics(
            metric_name=metric_name,
            unit=unit,
            sample_count=sample_count,
            expected_observations=expected_samples,
            coverage_ratio=coverage_ratio,
            sufficiency_status=sufficiency,
            p95=p95,
            p75=p75,
            p50=p50,
            median=median,
            mean=mean_val,
            minimum=min_val,
            maximum=max_val,
            stddev=stddev_val,
            coefficient_of_variation=cv_val,
            window_start=window_start,
            window_end=window_end,
            latest_timestamp=latest_ts,
            freshness_age_seconds=freshness_age,
            is_stale=is_stale,
            is_activity_metric=is_activity_metric,
        )

    # Alias for flexibility
    process_series = process_observations
