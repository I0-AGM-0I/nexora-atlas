"""
NEXORA ATLAS - Scenario Calculators
Calculates projected monthly/annual costs, savings reconciliation, and risk profiles.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple, Dict, Any

RISK_ORDER = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
COMPLEXITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


def calculate_scenario_financials(
    baseline_monthly_cost: Decimal,
    change_deltas: List[Decimal],
) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
    """
    Calculates exact Decimal financial outcomes:
    Returns (projected_monthly_cost, monthly_savings, annual_savings, percentage_savings).
    Guarantees:
    - baseline - projected == monthly_savings
    - annual_savings == monthly_savings * 12
    - sum(change_deltas) == -monthly_savings
    """
    total_delta = sum(change_deltas, Decimal("0.0000")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    projected_monthly_cost = (baseline_monthly_cost + total_delta).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    monthly_savings = (baseline_monthly_cost - projected_monthly_cost).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    annual_savings = (monthly_savings * Decimal("12")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    if baseline_monthly_cost > Decimal("0"):
        percentage_savings = ((monthly_savings / baseline_monthly_cost) * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        percentage_savings = Decimal("0.00")

    return projected_monthly_cost, monthly_savings, annual_savings, percentage_savings


def aggregate_scenario_risk(
    risk_levels: List[str],
    complexity_levels: List[str],
) -> Tuple[str, str, str]:
    """
    Deterministically aggregates performance risk, reliability risk, and complexity level
    using the maximum observed risk in the scenario.
    Returns (performance_risk, reliability_risk, complexity_level).
    """
    perf_max = 1  # LOW
    rel_max = 1   # LOW
    comp_max = 1  # LOW

    for r in risk_levels:
        lvl = RISK_ORDER.get(r.upper(), 1)
        if lvl > perf_max:
            perf_max = lvl
        if lvl > rel_max:
            rel_max = lvl

    for c in complexity_levels:
        clvl = COMPLEXITY_ORDER.get(c.upper(), 1)
        if clvl > comp_max:
            comp_max = clvl

    inv_risk = {0: "NONE", 1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}
    inv_comp = {1: "LOW", 2: "MEDIUM", 3: "HIGH"}

    return inv_risk[perf_max], inv_risk[rel_max], inv_comp[comp_max]
