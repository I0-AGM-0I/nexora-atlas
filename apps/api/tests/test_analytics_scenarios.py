"""
NEXORA ATLAS - Phase 6 Scenario Modeling & Constraint Tests
Verifies financial invariants, constraint validators, and explicit scenario assumptions.
"""

import pytest
from decimal import Decimal

from app.analytics.types import ScenarioType
from app.analytics.scenarios.calculators import calculate_scenario_financials, aggregate_scenario_risk
from app.analytics.scenarios.validators import validate_scenario_change, validate_scenario_financials
from app.analytics.scenarios.engine import ScenarioEngine


def test_scenario_financial_invariants():
    """
    Verifies Correction 14:
    baseline - projected == monthly_savings
    monthly_savings * 12 == annual_savings
    sum(change_deltas) == -monthly_savings
    """
    baseline = Decimal("1250000.0000")
    # 3 changes saving 100,000, 50,000, and 20,000 (total savings: 170,000)
    change_deltas = [Decimal("-100000.0000"), Decimal("-50000.0000"), Decimal("-20000.0000")]

    projected, monthly_sav, annual_sav, pct_sav = calculate_scenario_financials(
        baseline, change_deltas
    )

    # 1250000 - 170000 = 1080000
    assert projected == Decimal("1080000.0000")
    assert monthly_sav == Decimal("170000.0000")
    # 170000 * 12 = 2040000
    assert annual_sav == Decimal("2040000.0000")
    # 170000 / 1250000 * 100 = 13.60%
    assert pct_sav == Decimal("13.60")

    # Invariant validator check: zero violations
    violations = validate_scenario_financials(
        baseline_monthly_cost=baseline,
        projected_monthly_cost=projected,
        monthly_savings=monthly_sav,
        annual_savings=annual_sav,
        change_deltas=change_deltas,
    )
    assert len(violations) == 0


def test_scenario_architectural_constraints():
    """Verifies that invalid architectural alterations are flagged with explicit constraint violations."""
    # 1. Reject off-hours shutdown on Production resource
    prod_resource = {
        "id": "res-prod-ec2",
        "name": "prod-api-server",
        "tags": {"Environment": "production"},
    }
    violations_prod = validate_scenario_change("OFF_HOURS_SHUTDOWN", prod_resource)
    assert len(violations_prod) == 1
    assert violations_prod[0].rule_name == "NO_PROD_OFF_HOURS_SHUTDOWN"

    # Non-production resource should pass
    dev_resource = {
        "id": "res-dev-ec2",
        "name": "dev-worker",
        "tags": {"Environment": "development"},
    }
    violations_dev = validate_scenario_change("OFF_HOURS_SHUTDOWN", dev_resource)
    assert len(violations_dev) == 0

    # 2. Reject termination of HA database replica
    ha_db = {
        "id": "res-prod-db",
        "name": "prod-postgres-replica",
        "service_name": "AmazonRDS",
        "specs_json": {"multi_az": True},
    }
    violations_ha = validate_scenario_change("TERMINATE_REPLICA", ha_db)
    assert len(violations_ha) == 1
    assert violations_ha[0].rule_name == "PRESERVE_HA_DATABASE_REPLICA"


def test_scenario_engine_simulation_and_assumptions():
    """Verifies end-to-end scenario simulation attaching explicit assumptions."""
    baseline = Decimal("500000.0000")
    changes = [
        {
            "resource_id": "res-1",
            "resource_name": "orphan-ebs",
            "change_type": "TERMINATE_UNATTACHED_STORAGE",
            "current_spec": "gp2 500GB",
            "proposed_spec": "None",
            "current_monthly_cost": Decimal("4000.0000"),
            "projected_monthly_cost": Decimal("0.0000"),
            "delta_cost": Decimal("-4000.0000"),
            "risk_level": "LOW",
            "complexity_level": "LOW",
        }
    ]

    sim = ScenarioEngine.simulate_scenario(
        name="Conservative Savings Plan",
        scenario_type=ScenarioType.CONSERVATIVE,
        baseline_monthly_cost=baseline,
        proposed_changes=changes,
    )

    assert sim.is_valid is True
    assert sim.monthly_savings == Decimal("4000.0000")
    assert sim.annual_savings == Decimal("48000.0000")
    assert sim.projected_monthly_cost == Decimal("496000.0000")

    # Explicit assumptions verification (Correction 8 & 23)
    assert sim.assumptions["pricing_basis"] == "synthetic_demo"
    assert sim.assumptions["operating_hours_per_month"] == 720
