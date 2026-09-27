"""
NEXORA ATLAS - Evidence Builder
Maintains rigorous separation between empirical observed facts and algorithmic inferences.
"""

from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timezone
from app.intelligence.constants import RULESET_VERSION


class EvidenceBuilder:
    """Constructs structured evidence dossiers for anomalies and waste opportunities."""

    @staticmethod
    def build_anomaly_evidence(
        rule_name: str,
        detected_spend: Decimal,
        expected_spend: Decimal,
        deviation_pct: Decimal,
        window_days: int,
        baseline_stats: Dict[str, Any],
        historical_points: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Structures anomaly evidence separating facts (observed spending & statistics)
        from algorithmic inferences.
        """
        facts: Dict[str, Any] = {
            "detected_spend_inr": str(detected_spend.quantize(Decimal("0.0001"))),
            "expected_baseline_inr": str(expected_spend.quantize(Decimal("0.0001"))),
            "deviation_percentage": str(deviation_pct.quantize(Decimal("0.01"))),
            "observation_window_days": window_days,
            "baseline_statistics": baseline_stats,
        }
        if historical_points:
            facts["historical_samples"] = historical_points[-7:]  # Last 7 points for concise audit

        inferences: Dict[str, Any] = {
            "detection_rule": rule_name,
            "ruleset_version": RULESET_VERSION,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
        if context:
            inferences.update(context)

        return {
            "observed_facts": facts,
            "inferences": inferences,
        }

    @staticmethod
    def build_waste_evidence(
        waste_type: str,
        observed_telemetry: Dict[str, Any],
        assumptions: Dict[str, Any],
        estimated_monthly_waste: Decimal,
    ) -> Dict[str, Any]:
        """
        Structures waste evidence separating empirical telemetry from financial assumptions.
        """
        return {
            "observed_telemetry": observed_telemetry,
            "financial_assumptions": assumptions,
            "estimated_monthly_waste_inr": str(estimated_monthly_waste.quantize(Decimal("0.0001"))),
            "ruleset_version": RULESET_VERSION,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
