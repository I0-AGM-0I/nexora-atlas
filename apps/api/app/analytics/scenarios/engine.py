"""
NEXORA ATLAS - Scenario Engine
Simulates Conservative, Aggressive, Modernization, and Custom what-if infrastructure scenarios.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional

from app.analytics.constants import (
    SCENARIO_VERSION,
    PRICING_BASIS_SYNTHETIC,
    BUSINESS_HOURS_PER_MONTH,
    DEFAULT_MONTHLY_HOURS,
    DAYS_PER_MONTH,
)
from app.analytics.types import ScenarioType
from app.analytics.models import (
    ScenarioSimulationResult,
    ScenarioChangeCalculation,
    ScenarioConstraintViolation,
    AnalyticalExplanation,
)
from app.analytics.scenarios.calculators import (
    calculate_scenario_financials,
    aggregate_scenario_risk,
)
from app.analytics.scenarios.validators import (
    validate_scenario_change,
    validate_scenario_financials,
)


class ScenarioEngine:
    """Deterministic simulation engine for infrastructure optimization scenarios."""

    @classmethod
    def simulate_scenario(
        cls,
        name: str,
        scenario_type: ScenarioType,
        baseline_monthly_cost: Decimal,
        proposed_changes: List[Dict[str, Any]],
        resource_map: Optional[Dict[str, Dict[str, Any]]] = None,
        custom_assumptions: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> ScenarioSimulationResult:
        """
        Simulates a what-if scenario:
        - Validates all proposed changes against safety constraints (no prod shutdown, preserve HA db).
        - Computes exact Decimal financial outcomes and validates invariants.
        - Attaches explicit assumptions and analytical provenance.
        """
        resource_map = resource_map or {}
        violations: List[ScenarioConstraintViolation] = []
        change_calculations: List[ScenarioChangeCalculation] = []
        change_deltas: List[Decimal] = []
        risk_levels: List[str] = []
        complexity_levels: List[str] = []

        assumptions: Dict[str, Any] = {
            "pricing_basis": PRICING_BASIS_SYNTHETIC,
            "operating_hours_per_month": int(DEFAULT_MONTHLY_HOURS),
            "days_per_month": DAYS_PER_MONTH,
            "migration_execution_cost": "0.0000",
        }
        if custom_assumptions:
            assumptions.update(custom_assumptions)

        for c in proposed_changes:
            res_id = str(c.get("resource_id", ""))
            resource = resource_map.get(res_id)
            change_type = str(c.get("change_type", "GENERIC_OPTIMIZATION"))

            # Validate architectural constraints
            change_violations = validate_scenario_change(
                change_type=change_type,
                resource=resource,
                proposed_spec=c.get("proposed_spec"),
            )
            violations.extend(change_violations)

            curr_cost = Decimal(str(c.get("current_monthly_cost", "0.0000")))
            proj_cost = Decimal(str(c.get("projected_monthly_cost", "0.0000")))
            delta = Decimal(str(c.get("delta_cost", str(proj_cost - curr_cost))))

            # Normalize delta: delta = projected - current
            if delta > Decimal("0") and curr_cost > proj_cost:
                delta = -delta

            change_deltas.append(delta)
            risk = str(c.get("risk_level", "LOW")).upper()
            comp = str(c.get("complexity_level", "LOW")).upper()
            risk_levels.append(risk)
            complexity_levels.append(comp)

            change_calculations.append(
                ScenarioChangeCalculation(
                    resource_id=res_id if res_id else None,
                    resource_name=resource.get("name") if resource else c.get("resource_name"),
                    change_type=change_type,
                    current_spec=str(c.get("current_spec", "Unknown")),
                    proposed_spec=str(c.get("proposed_spec", "Optimized")),
                    current_monthly_cost=curr_cost,
                    projected_monthly_cost=proj_cost,
                    delta_cost=delta,
                    risk_level=risk,
                    complexity_level=comp,
                    assumptions=c.get("assumptions") or assumptions,
                )
            )

        # Calculate financials
        proj_monthly, monthly_sav, annual_sav, pct_sav = calculate_scenario_financials(
            baseline_monthly_cost, change_deltas
        )

        # Validate financial invariants
        financial_violations = validate_scenario_financials(
            baseline_monthly_cost=baseline_monthly_cost,
            projected_monthly_cost=proj_monthly,
            monthly_savings=monthly_sav,
            annual_savings=annual_sav,
            change_deltas=change_deltas,
        )
        violations.extend(financial_violations)

        perf_risk, rel_risk, complexity = aggregate_scenario_risk(risk_levels, complexity_levels)
        is_valid = len([v for v in violations if v.severity == "ERROR"]) == 0

        explanation = AnalyticalExplanation(
            observations={
                "baseline_monthly_cost": str(baseline_monthly_cost),
                "changes_count": len(proposed_changes),
            },
            derived_metrics={
                "projected_monthly_cost": str(proj_monthly),
                "monthly_savings": str(monthly_sav),
                "annual_savings": str(annual_sav),
                "percentage_savings": str(pct_sav),
            },
            classification="VALID_SCENARIO" if is_valid else "INVALID_SCENARIO",
            evidence=[
                f"Simulated {len(proposed_changes)} changes yielding ₹{monthly_sav}/month savings ({pct_sav}%)",
                f"Performance Risk: {perf_risk}, Reliability Risk: {rel_risk}, Complexity: {complexity}",
            ]
            + [f"Violation: {v.reason}" for v in violations],
            method="deterministic_scenario_simulation_v1",
            parameters={"scenario_type": scenario_type.value},
            assumptions=assumptions,
            version=SCENARIO_VERSION,
        )

        return ScenarioSimulationResult(
            name=name,
            scenario_type=scenario_type,
            description=description,
            baseline_monthly_cost=baseline_monthly_cost,
            projected_monthly_cost=proj_monthly,
            monthly_savings=monthly_sav,
            annual_savings=annual_sav,
            percentage_savings=pct_sav,
            performance_risk=perf_risk,
            reliability_risk=rel_risk,
            complexity_level=complexity,
            assumptions=assumptions,
            changes=change_calculations,
            violations=violations,
            is_valid=is_valid,
            explanation=explanation,
        )
