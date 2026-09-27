"""
NEXORA ATLAS - Trend Direction & Regime Classification
Deterministic classification applying strict precedence and transparent mathematical formulas.
"""

from decimal import Decimal
from typing import List, Tuple, Optional
from datetime import date

from app.analytics.constants import (
    CV_VOLATILE_THRESHOLD,
    STABLE_DELTA_PCT,
    REGIME_NORMAL_BAND_PCT,
    REGIME_ELEVATED_PCT,
    REGIME_ELEVATED_MIN_DAYS,
    REGIME_SPIKE_PCT,
)
from app.analytics.types import TrendDirection, CostRegime


def classify_trend_direction(
    coefficient_of_variation: Decimal,
    period_over_period_pct: Decimal,
) -> TrendDirection:
    """
    Classifies overall spend trend direction using deterministic precedence:
    1. CV >= CV_VOLATILE_THRESHOLD (0.25) -> VOLATILE
    2. delta_pct > +3.0% -> INCREASING
    3. delta_pct < -3.0% -> DECREASING
    4. otherwise -> STABLE
    """
    if coefficient_of_variation >= CV_VOLATILE_THRESHOLD:
        return TrendDirection.VOLATILE
    if period_over_period_pct > STABLE_DELTA_PCT:
        return TrendDirection.INCREASING
    if period_over_period_pct < -STABLE_DELTA_PCT:
        return TrendDirection.DECREASING
    return TrendDirection.STABLE


def classify_daily_regimes(
    daily_spend: List[Tuple[date, Decimal]],
    baseline_spend: Decimal,
) -> List[CostRegime]:
    """
    Classifies each daily observation into a CostRegime with strict precedence:
    SPIKE -> RECOVERY -> ELEVATED -> NORMAL

    Conditions:
    1. SPIKE: daily_spend >= baseline * 1.50 (+50% spike)
    2. RECOVERY: daily_spend < peak_recent AND spend is declining towards baseline
                 following a spike or elevated regime within the past 7 days, but
                 not yet back to normal.
    3. ELEVATED: daily_spend >= baseline * 1.10 (+10%) sustained for >= 3 consecutive days.
    4. NORMAL: within +/-10% of baseline, or not elevated.
    """
    if not daily_spend:
        return []

    if baseline_spend <= Decimal("0"):
        return [CostRegime.NORMAL for _ in daily_spend]

    spike_threshold = baseline_spend * (Decimal("1") + REGIME_SPIKE_PCT / Decimal("100"))
    elevated_threshold = baseline_spend * (Decimal("1") + REGIME_ELEVATED_PCT / Decimal("100"))
    normal_upper = baseline_spend * (Decimal("1") + REGIME_NORMAL_BAND_PCT / Decimal("100"))

    regimes: List[CostRegime] = []
    consecutive_elevated = 0
    recent_spike_idx: Optional[int] = None

    for i, (_, cost) in enumerate(daily_spend):
        # 1. SPIKE Check
        if cost >= spike_threshold:
            regimes.append(CostRegime.SPIKE)
            recent_spike_idx = i
            consecutive_elevated += 1
            continue

        # Check elevated run
        is_above_elevated = cost >= elevated_threshold
        if is_above_elevated:
            consecutive_elevated += 1
        else:
            consecutive_elevated = 0

        # 2. RECOVERY Check
        # Following a SPIKE within the past 7 days, if cost is strictly declining towards baseline
        is_in_recovery = False
        if recent_spike_idx is not None and (i - recent_spike_idx) <= 7:
            if cost < spike_threshold and cost > normal_upper:
                prev_cost = daily_spend[i - 1][1] if i > 0 else cost
                if cost < prev_cost:
                    is_in_recovery = True

        if is_in_recovery:
            regimes.append(CostRegime.RECOVERY)
            continue

        # 3. ELEVATED Check
        if consecutive_elevated >= REGIME_ELEVATED_MIN_DAYS:
            regimes.append(CostRegime.ELEVATED)
            continue

        # 4. NORMAL Check (Default)
        regimes.append(CostRegime.NORMAL)

    return regimes
