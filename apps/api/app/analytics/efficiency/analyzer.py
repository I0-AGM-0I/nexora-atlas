"""
NEXORA ATLAS - Efficiency & Headroom Analyzer
Combines capacity headroom, idle resource cost, addressable waste, and unit economics contracts.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional

from app.analytics.constants import ANALYTICS_VERSION
from app.analytics.types import SufficiencyStatus
from app.analytics.models import (
    EfficiencyReport,
    HeadroomItem,
    UnitEconomicsContract,
    AnalyticalExplanation,
)
from app.analytics.efficiency.metrics import extract_resource_headroom


class EfficiencyAnalyzer:
    """Deterministic analyzer for infrastructure efficiency and capacity headroom."""

    @classmethod
    def analyze(
        cls,
        resources: List[Dict[str, Any]],
        phase5_opportunities: Optional[List[Dict[str, Any]]] = None,
    ) -> EfficiencyReport:
        """
        Analyzes infrastructure efficiency:
        - Extracts observed utilization headroom for EC2 / RDS resources.
        - Identifies idle/unattached resource counts and their run-rate costs.
        - Strictly decouples utilization % from addressable waste % (Correction 6).
        - Exposes unit economics contracts as NOT_CONFIGURED in demo mode (Correction 12).
        """
        headroom_items: List[HeadroomItem] = []
        for r in resources:
            specs = r.get("specs_json") or {}
            item = extract_resource_headroom(
                resource_id=str(r.get("id")),
                resource_name=str(r.get("name")),
                service_name=str(r.get("service_name")),
                specs=specs,
            )
            if item.sufficiency_status != SufficiencyStatus.NOT_APPLICABLE:
                headroom_items.append(item)

        # Ingest Phase 5 waste opportunities to determine addressable waste and idle cost
        idle_count = 0
        idle_monthly_cost = Decimal("0.0000")
        total_addressable_waste = Decimal("0.0000")

        if phase5_opportunities:
            for opp in phase5_opportunities:
                waste_amt = Decimal(str(opp.get("estimated_waste_monthly", "0.0000")))
                total_addressable_waste += waste_amt
                waste_type = str(opp.get("waste_type", "")).upper()
                if "IDLE" in waste_type or "UNATTACHED" in waste_type:
                    idle_count += 1
                    idle_monthly_cost += waste_amt

        # Unit economics foundation: Strictly NOT_CONFIGURED in demo mode
        unit_economics = [
            UnitEconomicsContract(
                metric_name="Cost per API Request",
                unit_name="request",
                status=SufficiencyStatus.NOT_CONFIGURED,
                cost_per_unit=None,
                explanation="API request telemetry pipeline is not linked. Business metric integration required.",
            ),
            UnitEconomicsContract(
                metric_name="Cost per Active User",
                unit_name="user",
                status=SufficiencyStatus.NOT_CONFIGURED,
                cost_per_unit=None,
                explanation="Identity provider / active user metrics are not configured.",
            ),
            UnitEconomicsContract(
                metric_name="Cost per GB Ingested",
                unit_name="gb_ingested",
                status=SufficiencyStatus.NOT_CONFIGURED,
                cost_per_unit=None,
                explanation="Data pipeline ingestion telemetry is not configured.",
            ),
        ]

        explanation = AnalyticalExplanation(
            observations={
                "evaluated_resources_count": len(resources),
                "compute_headroom_evaluated": len(headroom_items),
                "idle_waste_sources_count": idle_count,
            },
            derived_metrics={
                "idle_monthly_cost": str(idle_monthly_cost),
                "estimated_addressable_waste": str(total_addressable_waste),
            },
            classification="EFFICIENCY_ANALYSIS",
            evidence=[
                f"Evaluated capacity headroom for {len(headroom_items)} compute/db instances",
                f"Identified {idle_count} idle or unattached components generating ₹{idle_monthly_cost}/month run-rate spend",
                "Unit economics telemetry unconfigured (zero phantom metrics manufactured)",
            ],
            method="headroom_and_waste_synthesis_v1",
            version=ANALYTICS_VERSION,
        )

        return EfficiencyReport(
            sufficiency_status=SufficiencyStatus.AVAILABLE if resources else SufficiencyStatus.INSUFFICIENT_DATA,
            headroom_items=headroom_items,
            idle_resources_count=idle_count,
            idle_resources_cost=idle_monthly_cost.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            estimated_addressable_waste=total_addressable_waste.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            unit_economics=unit_economics,
            explanation=explanation,
        )
