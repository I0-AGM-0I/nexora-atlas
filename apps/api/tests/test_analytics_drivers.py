"""
NEXORA ATLAS - Phase 6 Cost Driver Attribution Tests
Verifies distinct contribution metrics, evidence-gated classification, and exact Decimal reconciliation.
"""

import pytest
from decimal import Decimal

from app.analytics.types import ChangeClassification, DriverDimension, SufficiencyStatus
from app.analytics.drivers.ranking import calculate_contributions, classify_resource_change
from app.analytics.drivers.attribution import attribute_dimension_drivers
from app.analytics.drivers.analyzer import CostDriverAnalyzer


def test_distinct_contribution_metrics_calculation():
    """
    Verifies Correction 1:
    absolute_contribution_pct = abs(driver_delta) / sum(abs(all_driver_deltas)) * 100
    net_change_contribution_pct = driver_delta / total_delta * 100 (when total_delta != 0)
    Never conflated; handles zero denominators explicitly.
    """
    # Case A: Mixed increases and decreases
    # Service A: +100, Service B: -50, Service C: +50 -> Total Net: +100
    # Sum abs deltas: 100 + 50 + 50 = 200
    deltas = [Decimal("100.0000"), Decimal("-50.0000"), Decimal("50.0000")]
    total_delta = Decimal("100.0000")

    contributions = calculate_contributions(deltas, total_delta)

    # Service A: abs = 100/200 * 100 = 50%, net = 100/100 * 100 = 100%
    assert contributions[0][0] == Decimal("50.00")
    assert contributions[0][1] == Decimal("100.00")

    # Service B: abs = 50/200 * 100 = 25%, net = -50/100 * 100 = -50%
    assert contributions[1][0] == Decimal("25.00")
    assert contributions[1][1] == Decimal("-50.00")

    # Service C: abs = 50/200 * 100 = 25%, net = 50/100 * 100 = 50%
    assert contributions[2][0] == Decimal("25.00")
    assert contributions[2][1] == Decimal("50.00")

    # Case B: Zero net change (Total Delta == 0)
    # Service A: +100, Service B: -100 -> Total Net: 0
    # Sum abs: 200
    zero_net_deltas = [Decimal("100.0000"), Decimal("-100.0000")]
    contributions_zero_net = calculate_contributions(zero_net_deltas, Decimal("0.0000"))
    assert contributions_zero_net[0][0] == Decimal("50.00")
    assert contributions_zero_net[0][1] is None  # Zero denominator handled cleanly
    assert contributions_zero_net[1][0] == Decimal("50.00")
    assert contributions_zero_net[1][1] is None

    # Case C: Zero total change everywhere
    all_zero_deltas = [Decimal("0.0000"), Decimal("0.0000")]
    contributions_all_zero = calculate_contributions(all_zero_deltas, Decimal("0.0000"))
    assert contributions_all_zero[0][0] == Decimal("0.00")
    assert contributions_all_zero[0][1] is None


def test_change_classification_evidence_gate():
    """
    Verifies Correction 2:
    Do not classify a cost change as USAGE unless:
    specification unchanged + usage/time-volume evidence exists + usage changed materially.
    Do not infer usage from cost alone. Otherwise: NOT_AVAILABLE.
    """
    # 1. New Resource
    assert (
        classify_resource_change(Decimal("1500.0000"), Decimal("0.0000"))
        == ChangeClassification.NEW_RESOURCE
    )

    # 2. Removed Resource
    assert (
        classify_resource_change(Decimal("0.0000"), Decimal("1500.0000"))
        == ChangeClassification.REMOVED_RESOURCE
    )

    # 3. Price/Configuration change
    assert (
        classify_resource_change(
            Decimal("3000.0000"),
            Decimal("2000.0000"),
            current_spec="m5.2xlarge",
            previous_spec="m5.xlarge",
        )
        == ChangeClassification.PRICE_CONFIG
    )

    # 4. Valid Usage change (spec unchanged + usage telemetry exists + volume changed materially > 5%)
    assert (
        classify_resource_change(
            Decimal("2500.0000"),
            Decimal("2000.0000"),
            current_spec="m5.large",
            previous_spec="m5.large",
            usage_telemetry={"current_volume": 720, "previous_volume": 550},
        )
        == ChangeClassification.USAGE
    )

    # 5. Cost changed but NO operational telemetry provided -> NOT_AVAILABLE (never guess usage from cost)
    assert (
        classify_resource_change(
            Decimal("2500.0000"),
            Decimal("2000.0000"),
            current_spec="m5.large",
            previous_spec="m5.large",
            usage_telemetry=None,
        )
        == ChangeClassification.NOT_AVAILABLE
    )


def test_cost_driver_decomposition_reconciliation():
    """Verifies that sum(driver_deltas) == total_delta across Service, Account, and Resource dimensions."""
    services = [
        {"name": "AmazonEC2", "current_cost": Decimal("50000.0000"), "previous_cost": Decimal("35000.0000")},
        {"name": "AmazonRDS", "current_cost": Decimal("25000.0000"), "previous_cost": Decimal("20000.0000")},
        {"name": "AmazonS3", "current_cost": Decimal("10000.0000"), "previous_cost": Decimal("12000.0000")},
    ]
    accounts = [
        {"name": "Production", "current_cost": Decimal("60000.0000"), "previous_cost": Decimal("45000.0000")},
        {"name": "Staging", "current_cost": Decimal("25000.0000"), "previous_cost": Decimal("22000.0000")},
    ]
    resources = [
        {
            "id": "res-1",
            "name": "prod-api-1",
            "current_cost": Decimal("30000.0000"),
            "previous_cost": Decimal("20000.0000"),
            "current_spec": "m5.2xlarge",
            "previous_spec": "m5.2xlarge",
        },
        {
            "id": "res-2",
            "name": "prod-db-1",
            "current_cost": Decimal("25000.0000"),
            "previous_cost": Decimal("20000.0000"),
            "current_spec": "db.r5.xlarge",
            "previous_spec": "db.r5.xlarge",
        },
        {
            "id": "res-3",
            "name": "staging-web",
            "current_cost": Decimal("20000.0000"),
            "previous_cost": Decimal("15000.0000"),
            "current_spec": "t3.medium",
            "previous_spec": "t3.medium",
        },
        {
            "id": "res-4",
            "name": "orphan-ebs",
            "current_cost": Decimal("10000.0000"),
            "previous_cost": Decimal("12000.0000"),
            "current_spec": "gp2",
            "previous_spec": "gp2",
        },
    ]

    result = CostDriverAnalyzer.decompose(services, accounts, resources)

    # Current total: 50000 + 25000 + 10000 = 85000
    # Previous total: 35000 + 20000 + 12000 = 67000
    # Net change: 18000
    assert result.current_period_cost == Decimal("85000.0000")
    assert result.previous_period_cost == Decimal("67000.0000")
    assert result.net_change == Decimal("18000.0000")
    assert result.reconciled is True

    # Service deltas sum == 18000
    svc_sum = sum((d.cost_delta for d in result.service_drivers), Decimal("0.0000"))
    assert svc_sum == Decimal("18000.0000")

    # Account deltas sum == 18000
    acc_sum = sum((d.cost_delta for d in result.account_drivers), Decimal("0.0000"))
    assert acc_sum == Decimal("18000.0000")

    # Resource deltas sum == 18000
    res_sum = sum((d.cost_delta for d in result.resource_drivers), Decimal("0.0000"))
    assert res_sum == Decimal("18000.0000")
