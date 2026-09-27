"""
NEXORA ATLAS - Cost Driver Ranking & Classification
Calculates distinct contribution percentages and enforces strict evidence gates for change classifications.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple, Optional, Dict, Any

from app.analytics.types import ChangeClassification


def calculate_contributions(
    deltas: List[Decimal],
    total_delta: Decimal,
) -> List[Tuple[Decimal, Optional[Decimal]]]:
    """
    Computes two distinct contribution metrics for a list of deltas:
    1. absolute_contribution_pct = abs(driver_delta) / sum(abs(all_driver_deltas)) * 100
    2. net_change_contribution_pct = driver_delta / total_delta * 100 (when total_delta != 0, else None)

    Never conflates the two. Explicitly handles zero denominators.
    """
    sum_abs_deltas = sum((abs(d) for d in deltas), Decimal("0.0000"))

    results: List[Tuple[Decimal, Optional[Decimal]]] = []
    for d in deltas:
        # 1. Absolute contribution
        if sum_abs_deltas > Decimal("0"):
            abs_pct = ((abs(d) / sum_abs_deltas) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            abs_pct = Decimal("0.00")

        # 2. Net change contribution
        if total_delta != Decimal("0"):
            net_pct = ((d / total_delta) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            net_pct = None

        results.append((abs_pct, net_pct))

    return results


def classify_resource_change(
    current_cost: Decimal,
    previous_cost: Decimal,
    current_spec: Optional[str] = None,
    previous_spec: Optional[str] = None,
    usage_telemetry: Optional[Dict[str, Any]] = None,
) -> ChangeClassification:
    """
    Classifies a resource cost change using strict evidence gating:
    - NEW_RESOURCE: previous_cost == 0 and current_cost > 0
    - REMOVED_RESOURCE: current_cost == 0 and previous_cost > 0
    - PRICE_CONFIG: configuration/spec evidence exists and changed
    - LIKELY_USAGE_DRIVEN: operationally aligned cost increase (spec unchanged + coverage >= 70% + cost delta >= 5% + operational delta >= 5%)
    - USAGE: specification unchanged + usage/time-volume evidence exists + usage changed materially (> 5%)
    - Otherwise: NOT_AVAILABLE (never infer usage from cost alone)
    """
    if previous_cost == Decimal("0") and current_cost > Decimal("0"):
        return ChangeClassification.NEW_RESOURCE

    if current_cost == Decimal("0") and previous_cost > Decimal("0"):
        return ChangeClassification.REMOVED_RESOURCE

    # Check configuration change evidence
    if current_spec and previous_spec and current_spec != previous_spec:
        return ChangeClassification.PRICE_CONFIG

    # Check usage evidence gate:
    # Requires explicit operational telemetry (e.g. usage_hours, request_count, iops, metric observations)
    if usage_telemetry:
        cov_val = usage_telemetry.get("telemetry_coverage_ratio") or usage_telemetry.get("coverage_ratio")
        has_coverage = cov_val is not None
        coverage_ok = False
        if has_coverage:
            try:
                coverage_ok = Decimal(str(cov_val)) >= Decimal("0.70")
            except Exception:
                coverage_ok = False

        # Calculate cost delta %
        cost_delta = current_cost - previous_cost
        cost_delta_pct = Decimal("0.00")
        if previous_cost > Decimal("0"):
            cost_delta_pct = (abs(cost_delta) / previous_cost) * Decimal("100")

        # Operational delta %
        op_delta_pct = Decimal("0.00")
        if "operational_delta_pct" in usage_telemetry:
            try:
                op_delta_pct = abs(Decimal(str(usage_telemetry["operational_delta_pct"])))
            except Exception:
                op_delta_pct = Decimal("0.00")
        elif "current_volume" in usage_telemetry and "previous_volume" in usage_telemetry:
            try:
                c_val = Decimal(str(usage_telemetry["current_volume"]))
                p_val = Decimal(str(usage_telemetry["previous_volume"]))
                if p_val > Decimal("0"):
                    op_delta_pct = abs((c_val - p_val) / p_val) * Decimal("100")
            except Exception:
                op_delta_pct = Decimal("0.00")

        # If strict Phase 8 operational contract satisfied with high coverage:
        if has_coverage and coverage_ok and cost_delta_pct >= Decimal("5.0") and op_delta_pct >= Decimal("5.0"):
            return ChangeClassification.LIKELY_USAGE_DRIVEN

        # Fallback to general USAGE if volume changed materially (> 5%)
        if op_delta_pct >= Decimal("5.0"):
            return ChangeClassification.USAGE

    return ChangeClassification.NOT_AVAILABLE
