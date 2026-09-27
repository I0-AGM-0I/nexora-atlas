"""
NEXORA ATLAS - Phase 6 Analytics Trend & Volatility Tests
Verifies rolling metrics, strict classification precedence, regime states, and data sufficiency gating.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta

from app.analytics.constants import CV_VOLATILE_THRESHOLD, STABLE_DELTA_PCT
from app.analytics.types import TrendDirection, CostRegime, SufficiencyStatus
from app.analytics.trends.decomposition import (
    classify_trend_direction,
    classify_daily_regimes,
)
from app.analytics.trends.analyzer import TrendAnalyzer


def test_trend_direction_precedence():
    """Verifies deterministic precedence: CV >= 0.25 -> VOLATILE, else delta > +3% -> INCREASING, etc."""
    # 1. Volatile overrides positive delta
    assert classify_trend_direction(Decimal("0.30"), Decimal("15.00")) == TrendDirection.VOLATILE
    # 2. Volatile overrides negative delta
    assert classify_trend_direction(Decimal("0.26"), Decimal("-20.00")) == TrendDirection.VOLATILE
    # 3. Non-volatile positive delta > 3%
    assert classify_trend_direction(Decimal("0.10"), Decimal("8.50")) == TrendDirection.INCREASING
    # 4. Non-volatile negative delta < -3%
    assert classify_trend_direction(Decimal("0.12"), Decimal("-5.20")) == TrendDirection.DECREASING
    # 5. Non-volatile stable within [-3%, +3%]
    assert classify_trend_direction(Decimal("0.08"), Decimal("1.50")) == TrendDirection.STABLE
    assert classify_trend_direction(Decimal("0.05"), Decimal("-2.10")) == TrendDirection.STABLE


def test_regime_classification_precedence():
    """Verifies regime transition conditions: SPIKE -> RECOVERY -> ELEVATED -> NORMAL."""
    baseline = Decimal("1000.0000")
    start = date(2026, 1, 1)

    # 1. Normal days
    days = [(start + timedelta(days=i), Decimal("1020.0000")) for i in range(5)]
    regimes = classify_daily_regimes(days, baseline)
    assert all(r == CostRegime.NORMAL for r in regimes)

    # 2. Elevated days sustained for >= 3 days
    elevated_days = [(start + timedelta(days=i), Decimal("1150.0000")) for i in range(4)]
    elevated_regimes = classify_daily_regimes(elevated_days, baseline)
    assert elevated_regimes[0] == CostRegime.NORMAL  # Day 1: not yet 3 days
    assert elevated_regimes[1] == CostRegime.NORMAL  # Day 2: not yet 3 days
    assert elevated_regimes[2] == CostRegime.ELEVATED  # Day 3: sustained >= 3 days
    assert elevated_regimes[3] == CostRegime.ELEVATED

    # 3. Spike day (> +50% baseline)
    spike_days = [
        (start, Decimal("1000.0000")),
        (start + timedelta(days=1), Decimal("1650.0000")),  # +65% -> SPIKE
    ]
    spike_regimes = classify_daily_regimes(spike_days, baseline)
    assert spike_regimes[0] == CostRegime.NORMAL
    assert spike_regimes[1] == CostRegime.SPIKE

    # 4. Recovery day (declining towards baseline after spike)
    recovery_days = [
        (start, Decimal("1000.0000")),
        (start + timedelta(days=1), Decimal("1800.0000")),  # Spike
        (start + timedelta(days=2), Decimal("1400.0000")),  # Lower than spike peak, heading toward baseline
    ]
    recovery_regimes = classify_daily_regimes(recovery_days, baseline)
    assert recovery_regimes[1] == CostRegime.SPIKE
    assert recovery_regimes[2] == CostRegime.RECOVERY


def test_trend_analyzer_insufficient_data():
    """Verifies that fewer than MIN_TREND_SAMPLES (3) returns INSUFFICIENT_DATA."""
    start = date(2026, 1, 1)
    samples = [(start, Decimal("500.0000")), (start + timedelta(days=1), Decimal("520.0000"))]
    result = TrendAnalyzer.analyze(samples)
    assert result.sufficiency_status == SufficiencyStatus.INSUFFICIENT_DATA
    assert result.daily_series == []
    assert result.explanation.classification == "INSUFFICIENT_DATA"


def test_trend_analyzer_metrics_and_provenance():
    """Verifies rolling averages, CV, PoP, and analytical explanation structure."""
    start = date(2026, 1, 1)
    records = []
    # 60 days of deterministic data: 30 days around 1000, then 30 days around 1200
    for i in range(60):
        c = Decimal("1000.0000") if i < 30 else Decimal("1200.0000")
        records.append((start + timedelta(days=i), c))

    result = TrendAnalyzer.analyze(records, comparison_window_days=30)
    assert result.sufficiency_status == SufficiencyStatus.AVAILABLE
    assert len(result.daily_series) == 60

    # Verify PoP delta
    # Previous 30d sum: 30 * 1000 = 30000
    # Current 30d sum: 30 * 1200 = 36000
    # Delta: +6000 (+20.00%)
    assert result.period_over_period_delta == Decimal("6000.0000")
    assert result.period_over_period_pct == Decimal("20.00")
    assert result.trend_direction == TrendDirection.INCREASING

    # Verify rolling averages exist and are Decimal
    assert result.daily_series[29].rolling_mean_7d == Decimal("1000.0000")
    assert result.daily_series[29].rolling_mean_30d == Decimal("1000.0000")
    assert result.daily_series[59].rolling_mean_7d == Decimal("1200.0000")

    # Verify structured explanation
    assert result.explanation.version == "atlas-analytics-v1"
    assert result.explanation.method == "rolling_average_pop_v1"
    assert "pop_delta" in result.explanation.derived_metrics
