"""
NEXORA ATLAS - Trend & Volatility Analyzer
Calculates rolling metrics, volatility statistics, period-over-period deltas, and regime states.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple, Optional
from datetime import date
import math

from app.analytics.constants import (
    ANALYTICS_VERSION,
    MIN_TREND_SAMPLES,
    WINDOW_7D,
    WINDOW_14D,
    WINDOW_30D,
    CV_VOLATILE_THRESHOLD,
    STABLE_DELTA_PCT,
)
from app.analytics.types import SufficiencyStatus, TrendDirection, CostRegime
from app.analytics.models import (
    DailyTrendPoint,
    TrendAnalysisResult,
    AnalyticalExplanation,
)
from app.analytics.trends.decomposition import (
    classify_trend_direction,
    classify_daily_regimes,
)


class TrendAnalyzer:
    """Deterministic analyzer for spend trends and cost volatility."""

    @classmethod
    def analyze(
        cls,
        daily_records: List[Tuple[date, Decimal]],
        comparison_window_days: int = 30,
    ) -> TrendAnalysisResult:
        """
        Analyzes a chronological list of (date, daily_unblended_cost) tuples.
        Computes rolling averages, volatility metrics, PoP deltas, and regimes.
        """
        daily_records = sorted(daily_records, key=lambda x: x[0])
        n = len(daily_records)

        if n < MIN_TREND_SAMPLES:
            return TrendAnalysisResult(
                sufficiency_status=SufficiencyStatus.INSUFFICIENT_DATA,
                trend_direction=TrendDirection.STABLE,
                current_regime=CostRegime.NORMAL,
                mean_daily_spend=Decimal("0.0000"),
                stddev_daily_spend=Decimal("0.0000"),
                coefficient_of_variation=Decimal("0.0000"),
                max_daily_deviation=Decimal("0.0000"),
                period_over_period_delta=Decimal("0.0000"),
                period_over_period_pct=Decimal("0.00"),
                daily_series=[],
                explanation=AnalyticalExplanation(
                    observations={"sample_count": n},
                    derived_metrics={},
                    classification="INSUFFICIENT_DATA",
                    evidence=[f"Sample count ({n}) is below minimum threshold ({MIN_TREND_SAMPLES})"],
                    method="rolling_average_pop_v1",
                    parameters={"min_samples": MIN_TREND_SAMPLES},
                    version=ANALYTICS_VERSION,
                ),
            )

        costs = [r[1] for r in daily_records]
        total_spend = sum(costs, Decimal("0.0000"))
        mean_spend = (total_spend / Decimal(str(n))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # Standard Deviation & Coefficient of Variation
        variance_sum = sum((c - mean_spend) ** 2 for c in costs)
        variance = variance_sum / Decimal(str(n))
        stddev = Decimal(str(math.sqrt(float(variance)))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        cv = Decimal("0.0000")
        if mean_spend > Decimal("0"):
            cv = (stddev / mean_spend).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        max_deviation = max(abs(c - mean_spend) for c in costs).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # Period-over-Period Delta
        w = min(comparison_window_days, n // 2 if n >= 2 else n)
        if w > 0 and n >= 2 * w:
            current_window = costs[-w:]
            previous_window = costs[-2 * w : -w]
            current_sum = sum(current_window, Decimal("0.0000"))
            previous_sum = sum(previous_window, Decimal("0.0000"))
            pop_delta = (current_sum - previous_sum).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            if previous_sum > Decimal("0"):
                pop_pct = ((pop_delta / previous_sum) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                pop_pct = Decimal("0.00")
        else:
            current_sum = total_spend
            previous_sum = total_spend
            pop_delta = Decimal("0.0000")
            pop_pct = Decimal("0.00")

        # Direction Classification
        trend_direction = classify_trend_direction(cv, pop_pct)

        # Baseline calculation for regimes: 30-day baseline prior to recent window or full mean
        baseline_for_regimes = mean_spend
        if n >= 30:
            baseline_for_regimes = (sum(costs[:30], Decimal("0.0000")) / Decimal("30")).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

        regimes = classify_daily_regimes(daily_records, baseline_for_regimes)
        current_regime = regimes[-1] if regimes else CostRegime.NORMAL

        # Rolling averages
        daily_series: List[DailyTrendPoint] = []
        for i, (d, cost) in enumerate(daily_records):
            # 7d rolling mean
            window_7 = costs[max(0, i - 6) : i + 1]
            mean_7d = (sum(window_7, Decimal("0.0000")) / Decimal(str(len(window_7)))).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

            # 14d rolling mean
            window_14 = costs[max(0, i - 13) : i + 1]
            mean_14d = (sum(window_14, Decimal("0.0000")) / Decimal(str(len(window_14)))).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

            # 30d rolling mean
            window_30 = costs[max(0, i - 29) : i + 1]
            mean_30d = (sum(window_30, Decimal("0.0000")) / Decimal(str(len(window_30)))).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

            daily_series.append(
                DailyTrendPoint(
                    date=d.isoformat(),
                    observed_cost=cost,
                    rolling_mean_7d=mean_7d,
                    rolling_mean_14d=mean_14d,
                    rolling_mean_30d=mean_30d,
                    regime=regimes[i],
                )
            )

        explanation = AnalyticalExplanation(
            observations={
                "sample_count": n,
                "current_period_spend": str(current_sum),
                "previous_period_spend": str(previous_sum),
                "latest_daily_spend": str(costs[-1]),
                "baseline_spend": str(baseline_for_regimes),
            },
            derived_metrics={
                "mean_daily_spend": str(mean_spend),
                "stddev_daily_spend": str(stddev),
                "coefficient_of_variation": str(cv),
                "pop_delta": str(pop_delta),
                "pop_pct": str(pop_pct),
            },
            classification=trend_direction.value,
            evidence=[
                f"Trend direction is {trend_direction.value} based on CV={cv} and PoP delta={pop_pct}%",
                f"Current regime is {current_regime.value} against baseline {baseline_for_regimes}",
            ],
            method="rolling_average_pop_v1",
            parameters={
                "comparison_window_days": comparison_window_days,
                "cv_threshold": str(CV_VOLATILE_THRESHOLD),
                "stable_delta_pct": str(STABLE_DELTA_PCT),
            },
            version=ANALYTICS_VERSION,
        )

        return TrendAnalysisResult(
            sufficiency_status=SufficiencyStatus.AVAILABLE,
            trend_direction=trend_direction,
            current_regime=current_regime,
            mean_daily_spend=mean_spend,
            stddev_daily_spend=stddev,
            coefficient_of_variation=cv,
            max_daily_deviation=max_deviation,
            period_over_period_delta=pop_delta,
            period_over_period_pct=pop_pct,
            daily_series=daily_series,
            explanation=explanation,
        )
