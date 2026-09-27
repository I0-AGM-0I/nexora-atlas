"""
NEXORA ATLAS - Baseline Engine
Computes deterministic rolling statistical baselines from daily financial cost telemetry.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple, Optional
from datetime import date
from pydantic import BaseModel
from app.intelligence.constants import MIN_BASELINE_SAMPLES


class BaselineResult(BaseModel):
    """Deterministic statistical baseline summary."""
    algorithm: str
    window_days: int
    sample_count: int
    is_sufficient: bool
    baseline_value: Decimal
    mean_value: Decimal
    median_value: Decimal
    std_dev: Decimal
    mad: Decimal  # Median Absolute Deviation

    @property
    def is_valid(self) -> bool:
        return self.is_sufficient

    @property
    def mean(self) -> Decimal:
        return self.mean_value

    @property
    def median(self) -> Decimal:
        return self.median_value



class BaselineCalculator:
    """Computes explainable statistical baselines for resource, service, and account cost series."""

    @staticmethod
    def _compute_median(values: List[Decimal]) -> Decimal:
        if not values:
            return Decimal("0.0000")
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        mid = n // 2
        if n % 2 == 1:
            return sorted_vals[mid]
        else:
            return ((sorted_vals[mid - 1] + sorted_vals[mid]) / Decimal("2")).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

    @staticmethod
    def _compute_mad(values: List[Decimal], median_val: Decimal) -> Decimal:
        if not values:
            return Decimal("0.0000")
        deviations = [abs(v - median_val) for v in values]
        return BaselineCalculator._compute_median(deviations)

    @classmethod
    def calculate(
        cls,
        series: List[Tuple[date, Decimal]],
        window_days: int = 14,
        algorithm: str = "rolling_mean",
        min_samples: int = MIN_BASELINE_SAMPLES,
    ) -> BaselineResult:
        """
        Calculates baseline metrics over the most recent window_days in the series.
        series: List of (usage_date, unblended_cost) sorted or unsorted.
        """
        if not series:
            return BaselineResult(
                algorithm=algorithm,
                window_days=window_days,
                sample_count=0,
                is_sufficient=False,
                baseline_value=Decimal("0.0000"),
                mean_value=Decimal("0.0000"),
                median_value=Decimal("0.0000"),
                std_dev=Decimal("0.0000"),
                mad=Decimal("0.0000"),
            )

        # Sort by date ascending
        sorted_series = sorted(series, key=lambda x: x[0])
        # Take up to window_days from the tail
        window_slice = sorted_series[-window_days:]
        values = [x[1] for x in window_slice]
        sample_count = len(values)

        if sample_count < min_samples:
            return BaselineResult(
                algorithm=algorithm,
                window_days=window_days,
                sample_count=sample_count,
                is_sufficient=False,
                baseline_value=Decimal("0.0000"),
                mean_value=Decimal("0.0000"),
                median_value=Decimal("0.0000"),
                std_dev=Decimal("0.0000"),
                mad=Decimal("0.0000"),
            )

        total = sum(values)
        mean_val = (total / Decimal(str(sample_count))).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        median_val = cls._compute_median(values)
        mad_val = cls._compute_mad(values, median_val)

        # Variance & StdDev (sample variance n-1)
        if sample_count > 1:
            variance = sum((v - mean_val) ** 2 for v in values) / Decimal(str(sample_count - 1))
            # Square root using Decimal.sqrt()
            std_dev = variance.sqrt().quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        else:
            std_dev = Decimal("0.0000")

        baseline_val = median_val if algorithm == "rolling_median" else mean_val

        return BaselineResult(
            algorithm=algorithm,
            window_days=window_days,
            sample_count=sample_count,
            is_sufficient=True,
            baseline_value=baseline_val,
            mean_value=mean_val,
            median_value=median_val,
            std_dev=std_dev,
            mad=mad_val,
        )

    @classmethod
    def compute(
        cls,
        series: List[Tuple[date, Decimal]],
        window_days: int = 14,
        algorithm: str = "rolling_mean",
        min_samples: int = MIN_BASELINE_SAMPLES,
    ) -> BaselineResult:
        """Alias for calculate method."""
        return cls.calculate(
            series=series,
            window_days=window_days,
            algorithm=algorithm,
            min_samples=min_samples,
        )

