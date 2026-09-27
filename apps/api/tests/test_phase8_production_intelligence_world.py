"""
NEXORA ATLAS - Phase 8 Production Intelligence Golden World Test
End-to-end deterministic verification of Golden Scenarios A through E:
- Resource A: High cost + low sustained utilization (CPU 8.5%, Mem 25%, Cov 95%) -> Rightsizing Candidate (Downsize & Graviton).
- Resource B: Low activity development database (Single-AZ, 0 conn, 90% idle) -> Evaluated for low activity.
- Resource C: Low activity production database with Multi-AZ -> SKIPPED (HA preservation guarantee).
- Resource D: Low utilization with sparse telemetry (< 70% coverage) -> SKIPPED (Strict coverage gate).
- Resource E: Low CPU (8%) but High Memory (92%) -> SKIPPED (High memory constrained, no downsize).
"""

import pytest
from decimal import Decimal

from app.intelligence.types import RuleStatus, WasteType
from app.intelligence.waste.rules import OversizedInstanceRule, IdleDatabaseRule


def test_golden_scenario_resource_a_rightsizing():
    """
    Resource A: High-cost compute with sustained low CPU, normal memory, and high coverage.
    Must produce rightsizing opportunity with epistemic wording and two viable options.
    """
    resource_a = {
        "id": "res-a-prod-compute",
        "account_id": "acc-prod",
        "name": "prod-analytics-worker-01",
        "native_id": "i-0a1b2c3d4e5f0001",
        "specs_json": {
            "instance_type": "m5.4xlarge",
            "p95_cpu_utilization_pct": Decimal("8.5"),
            "p95_memory_utilization_pct": Decimal("25.0"),
            "telemetry_coverage_ratio": Decimal("0.95"),
        },
    }

    eval_res, opp = OversizedInstanceRule.evaluate(
        resource=resource_a,
        monthly_cost=Decimal("58000.0000"),
        account_name="Production",
    )

    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert opp is not None
    assert opp.waste_type == WasteType.OVERSIZED_INSTANCE
    assert opp.confidence_score == Decimal("94.00")
    assert len(opp.recommendations) == 2

    # Option 1: Conservative downsize
    rec1 = opp.recommendations[0]
    assert "m5.large" in rec1.title
    assert "Observed utilization is consistently low" in rec1.reasoning
    assert rec1.confidence_score == Decimal("94.00")
    assert rec1.risk_level == "LOW"

    # Option 2: Modernization to Graviton
    rec2 = opp.recommendations[1]
    assert "Graviton" in rec2.title
    assert rec2.confidence_score == Decimal("84.00")
    assert rec2.risk_level == "MEDIUM"


def test_golden_scenario_resource_b_single_az_db():
    """
    Resource B: Low activity development database (Single-AZ, 0 conn, 90% idle).
    Must produce 'Evaluate Low Activity Database' recommendation without autonomous decommission claim.
    """
    resource_b = {
        "id": "res-b-dev-db",
        "account_id": "acc-dev",
        "name": "dev-staging-postgres",
        "native_id": "db-0002",
        "specs_json": {
            "instance_class": "db.t3.medium",
            "active_client_connections": 0,
            "idle_duration_pct": Decimal("90.0"),
            "multi_az": False,
        },
    }

    eval_res, opp = IdleDatabaseRule.evaluate(
        resource=resource_b,
        monthly_cost=Decimal("12000.0000"),
        account_name="Development",
    )

    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert opp is not None
    assert opp.waste_type == WasteType.IDLE_DATABASE
    rec = opp.recommendations[0]
    assert rec.title == "Evaluate Low Activity Database"
    assert "Evidence warrants operational review" in rec.reasoning
    assert rec.assumptions_json.get("autonomous_authority") is False


def test_golden_scenario_resource_c_multiaz_preservation():
    """
    Resource C: Production database with Multi-AZ redundancy and low connections.
    Must be SKIPPED to preserve high-availability guarantees.
    """
    resource_c = {
        "id": "res-c-prod-db",
        "account_id": "acc-prod",
        "name": "prod-core-db",
        "native_id": "db-0003",
        "specs_json": {
            "instance_class": "db.r5.2xlarge",
            "active_client_connections": 0,
            "idle_duration_pct": Decimal("95.0"),
            "multi_az": True,  # Protected HA architecture
        },
    }

    eval_res, opp = IdleDatabaseRule.evaluate(
        resource=resource_c,
        monthly_cost=Decimal("140000.0000"),
        account_name="Production",
    )

    assert eval_res.status == RuleStatus.SKIPPED
    assert "Multi-AZ redundancy indicates high-availability production database" in eval_res.skip_reason
    assert opp is None


def test_golden_scenario_resource_d_sparse_coverage():
    """
    Resource D: Compute with low CPU (10%), but telemetry coverage is only 40% (< 70% required).
    Must be SKIPPED due to insufficient telemetry evidence.
    """
    resource_d = {
        "id": "res-d-sparse",
        "account_id": "acc-prod",
        "name": "edge-gateway-sparse",
        "native_id": "i-0004",
        "specs_json": {
            "instance_type": "m5.2xlarge",
            "p95_cpu_utilization_pct": Decimal("10.0"),
            "telemetry_coverage_ratio": Decimal("0.40"),  # 40% < 70% threshold
        },
    }

    eval_res, opp = OversizedInstanceRule.evaluate(
        resource=resource_d,
        monthly_cost=Decimal("30000.0000"),
        account_name="Production",
    )

    assert eval_res.status == RuleStatus.SKIPPED
    assert "Insufficient telemetry coverage: 40.0% < 70% minimum" in eval_res.skip_reason
    assert opp is None


def test_golden_scenario_resource_e_high_memory_constraint():
    """
    Resource E (Golden Scenario 5): Low CPU (8%) but High Memory (92% >= 80% threshold).
    Must be SKIPPED because compute is memory-constrained and cannot be downsized safely.
    """
    resource_e = {
        "id": "res-e-redis-cache",
        "account_id": "acc-prod",
        "name": "in-memory-cache-01",
        "native_id": "i-0005",
        "specs_json": {
            "instance_type": "r5.4xlarge",
            "p95_cpu_utilization_pct": Decimal("8.0"),
            "p95_memory_utilization_pct": Decimal("92.0"),  # 92% >= 80% threshold
            "telemetry_coverage_ratio": Decimal("0.98"),
        },
    }

    eval_res, opp = OversizedInstanceRule.evaluate(
        resource=resource_e,
        monthly_cost=Decimal("62000.0000"),
        account_name="Production",
    )

    assert eval_res.status == RuleStatus.SKIPPED
    assert "High memory constraint: p95 memory utilization 92.0% >= 80.0% precludes compute downsizing" in eval_res.skip_reason
    assert opp is None
