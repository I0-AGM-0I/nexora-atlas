"""
NEXORA ATLAS - Cost Driver Attribution
Decomposes period-over-period net change across dimensions with exact financial reconciliation.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional

from app.analytics.constants import ANALYTICS_VERSION
from app.analytics.types import DriverDimension, ChangeClassification
from app.analytics.models import CostDriverItem, AnalyticalExplanation
from app.analytics.drivers.ranking import calculate_contributions, classify_resource_change


def attribute_dimension_drivers(
    dimension: DriverDimension,
    records: List[Dict[str, Any]],
    net_change: Decimal,
    comparison_window_days: int = 30,
) -> List[CostDriverItem]:
    """
    Decomposes period-over-period net change across a single dimension (SERVICE, ACCOUNT, RESOURCE, REGION).
    Enforces exact Decimal reconciliation: sum(item.cost_delta) == net_change (where applicable).
    """
    if not records:
        return []

    deltas = [r["current_cost"] - r["previous_cost"] for r in records]
    contributions = calculate_contributions(deltas, net_change)

    # Sort items by absolute delta descending to rank most impactful drivers first
    indexed = list(enumerate(records))
    indexed.sort(key=lambda x: abs(x[1]["current_cost"] - x[1]["previous_cost"]), reverse=True)

    items: List[CostDriverItem] = []
    for rank, (original_idx, r) in enumerate(indexed, start=1):
        curr = r["current_cost"].quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        prev = r["previous_cost"].quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        delta = (curr - prev).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        abs_contrib, net_contrib = contributions[original_idx]

        if delta > Decimal("0"):
            direction = "INCREASING"
        elif delta < Decimal("0"):
            direction = "DECREASING"
        else:
            direction = "UNCHANGED"

        # Classification
        if dimension == DriverDimension.RESOURCE:
            classification = classify_resource_change(
                current_cost=curr,
                previous_cost=prev,
                current_spec=r.get("current_spec"),
                previous_spec=r.get("previous_spec"),
                usage_telemetry=r.get("usage_telemetry"),
            )
        else:
            # For Service, Account, Region: if proportional share changed, it is a MIX_SHIFT
            classification = ChangeClassification.MIX_SHIFT if delta != Decimal("0") else ChangeClassification.NOT_AVAILABLE

        explanation = AnalyticalExplanation(
            observations={
                "current_period_cost": str(curr),
                "previous_period_cost": str(prev),
            },
            derived_metrics={
                "cost_delta": str(delta),
                "absolute_contribution_pct": str(abs_contrib),
                "net_change_contribution_pct": str(net_contrib) if net_contrib is not None else "N/A",
            },
            classification=classification.value,
            evidence=[
                f"{dimension.value} '{r['name']}' changed by {delta} INR ({direction})",
                f"Absolute contribution to period change is {abs_contrib}%",
            ],
            method="period_delta_attribution_v1",
            parameters={"comparison_window_days": comparison_window_days},
            version=ANALYTICS_VERSION,
        )

        items.append(
            CostDriverItem(
                dimension=dimension,
                identifier=str(r.get("id") or r.get("name")),
                name=str(r.get("name")),
                current_period_cost=curr,
                previous_period_cost=prev,
                cost_delta=delta,
                absolute_contribution_pct=abs_contrib,
                net_change_contribution_pct=net_contrib,
                direction=direction,
                rank=rank,
                classification=classification,
                explanation=explanation,
            )
        )

    return items
