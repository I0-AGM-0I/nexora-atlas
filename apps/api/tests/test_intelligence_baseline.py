"""
NEXORA ATLAS - Tests: Baseline Calculator
Verifies statistical baseline computations: rolling mean, median, stddev, and MAD
with pure Decimal arithmetic and sample sufficiency gating.
"""

from decimal import Decimal
from datetime import date, timedelta
from app.intelligence.baseline.calculator import BaselineCalculator


def test_baseline_insufficient_samples():
    series = [
        (date(2026, 1, 1), Decimal("100.00")),
        (date(2026, 1, 2), Decimal("110.00")),
    ]
    baseline = BaselineCalculator.compute(series, min_samples=3)
    assert baseline.is_valid is False
    assert baseline.sample_count == 2
    assert baseline.mean == Decimal("0.0000")


def test_baseline_constant_series():
    series = [
        (date(2026, 1, i), Decimal("100.00"))
        for i in range(1, 15)
    ]
    baseline = BaselineCalculator.compute(series)
    assert baseline.is_valid is True
    assert baseline.sample_count == 14
    assert baseline.mean == Decimal("100.0000")
    assert baseline.median == Decimal("100.0000")
    assert baseline.std_dev == Decimal("0.0000")
    assert baseline.mad == Decimal("0.0000")


def test_baseline_known_distribution():
    # Samples: 10, 20, 30, 40, 50
    # Mean = 30
    # Median = 30
    # Deviations from median: |10-30|=20, |20-30|=10, |30-30|=0, |40-30|=10, |50-30|=20
    # Sorted deviations: 0, 10, 10, 20, 20
    # MAD = 10
    series = [
        (date(2026, 1, 1), Decimal("10.00")),
        (date(2026, 1, 2), Decimal("20.00")),
        (date(2026, 1, 3), Decimal("30.00")),
        (date(2026, 1, 4), Decimal("40.00")),
        (date(2026, 1, 5), Decimal("50.00")),
    ]
    baseline = BaselineCalculator.compute(series)
    assert baseline.is_valid is True
    assert baseline.mean == Decimal("30.0000")
    assert baseline.median == Decimal("30.0000")
    assert baseline.mad == Decimal("10.0000")
    # Variance = (400 + 100 + 0 + 100 + 400) / 4 = 1000 / 4 = 250
    # Stddev = sqrt(250) ≈ 15.811388...
    assert baseline.std_dev.quantize(Decimal("0.01")) == Decimal("15.81")


def test_baseline_even_sample_count_median():
    # Samples: 10, 20, 30, 40 -> median = (20+30)/2 = 25
    series = [
        (date(2026, 1, 1), Decimal("10.00")),
        (date(2026, 1, 2), Decimal("20.00")),
        (date(2026, 1, 3), Decimal("30.00")),
        (date(2026, 1, 4), Decimal("40.00")),
    ]
    baseline = BaselineCalculator.compute(series)
    assert baseline.median == Decimal("25.0000")
