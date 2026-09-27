"""
NEXORA ATLAS - Optimization Planner
Blueprints Conservative, Aggressive, and Modernization scenario inputs from recommendations.
"""

from decimal import Decimal
from typing import List, Dict, Any, Tuple

from app.analytics.types import ScenarioType


class OptimizationPlanner:
    """Blueprints compatible scenario changes from Phase 5 recommendations."""

    @classmethod
    def blueprint_scenarios(
        cls,
        recommendations: List[Dict[str, Any]],
        baseline_monthly_cost: Decimal,
    ) -> Dict[ScenarioType, List[Dict[str, Any]]]:
        """
        Maps recommendation candidates into three distinct scenario change sets:
        1. CONSERVATIVE: Low-risk, high-reversibility terminations and minor rightsizing.
        2. AGGRESSIVE: Full non-production scheduling and larger rightsizing.
        3. MODERNIZATION: Storage tier upgrades (gp2 -> gp3) and architecture upgrades (x86 -> Graviton).
        """
        conservative_changes: List[Dict[str, Any]] = []
        aggressive_changes: List[Dict[str, Any]] = []
        modernization_changes: List[Dict[str, Any]] = []

        for r in recommendations:
            res_id = str(r.get("resource_id", ""))
            curr_spec = str(r.get("current_configuration", "Standard"))
            prop_spec = str(r.get("recommended_configuration", "Optimized"))
            monthly_sav = Decimal(str(r.get("estimated_monthly_savings", "0.0000")))
            delta = -monthly_sav  # Savings represented as negative cost delta
            risk = str(r.get("risk_level", "LOW")).upper()
            title = str(r.get("title", "")).lower()

            base_change = {
                "resource_id": res_id,
                "resource_name": r.get("resource_name") or r.get("title"),
                "current_spec": curr_spec,
                "proposed_spec": prop_spec,
                "current_monthly_cost": r.get("current_monthly_cost", monthly_sav),
                "projected_monthly_cost": max(
                    Decimal("0.0000"),
                    Decimal(str(r.get("current_monthly_cost", monthly_sav))) - monthly_sav,
                ),
                "delta_cost": delta,
                "risk_level": risk,
            }

            # Classify into scenario types
            if "gp2" in curr_spec and "gp3" in prop_spec:
                modernization_changes.append(
                    {
                        **base_change,
                        "change_type": "STORAGE_TIER_MODERNIZATION",
                        "complexity_level": "LOW",
                    }
                )
            elif "graviton" in prop_spec.lower() or "c7g" in prop_spec.lower():
                modernization_changes.append(
                    {
                        **base_change,
                        "change_type": "ARM_GRAVITON_MIGRATION",
                        "complexity_level": "HIGH",
                    }
                )
            elif "unattached" in title or "orphan" in title:
                conservative_changes.append(
                    {
                        **base_change,
                        "change_type": "TERMINATE_UNATTACHED_STORAGE",
                        "complexity_level": "LOW",
                    }
                )
            elif "schedule" in title or "off-hours" in title:
                aggressive_changes.append(
                    {
                        **base_change,
                        "change_type": "NON_PROD_OFF_HOURS_SCHEDULE",
                        "complexity_level": "MEDIUM",
                    }
                )
            else:
                # Standard right-sizing
                if risk in ("HIGH", "MEDIUM"):
                    aggressive_changes.append(
                        {
                            **base_change,
                            "change_type": "AGGRESSIVE_RIGHTSIZE",
                            "complexity_level": "MEDIUM",
                        }
                    )
                else:
                    conservative_changes.append(
                        {
                            **base_change,
                            "change_type": "CONSERVATIVE_RIGHTSIZE",
                            "complexity_level": "LOW",
                        }
                    )

        return {
            ScenarioType.CONSERVATIVE: conservative_changes,
            ScenarioType.AGGRESSIVE: aggressive_changes,
            ScenarioType.MODERNIZATION: modernization_changes,
        }
