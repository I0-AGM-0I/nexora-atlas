"""
NEXORA ATLAS - Phase 6 Efficiency & Capacity Headroom Tests
Verifies observed utilization headroom, waste decoupling, and unconfigured unit economics contracts.
"""

import pytest
from decimal import Decimal

from app.analytics.types import SufficiencyStatus
from app.analytics.efficiency.metrics import calculate_observed_utilization_headroom, extract_resource_headroom
from app.analytics.efficiency.analyzer import EfficiencyAnalyzer


def test_observed_utilization_headroom_calculation():
    """Verifies Correction 5: observed_utilization_headroom = 100% - p95 utilization."""
    # p95 CPU = 18.5% -> Headroom = 81.5%
    headroom = calculate_observed_utilization_headroom(Decimal("18.50"))
    assert headroom == Decimal("81.50")

    # p95 Memory = 31.0% -> Headroom = 69.0%
    headroom_mem = calculate_observed_utilization_headroom(Decimal("31.00"))
    assert headroom_mem == Decimal("69.00")

    # Missing telemetry returns None
    assert calculate_observed_utilization_headroom(None) is None


def test_efficiency_analyzer_waste_decoupling_and_unit_economics():
    """
    Verifies Correction 6 & 12:
    - Never calculates idle_cost = 100 - utilization.
    - Decouples utilization, idle duration, resource cost, and addressable waste.
    - Unit economics returns NOT_CONFIGURED in demo mode (zero fake metrics).
    """
    resources = [
        {
            "id": "res-1",
            "name": "prod-api-1",
            "service_name": "AmazonEC2",
            "specs_json": {
                "instance_type": "c5.2xlarge",
                "cpu_utilization_p95": 14.5,
                "memory_utilization_p95": 28.0,
            },
        },
        {
            "id": "res-2",
            "name": "dev-db",
            "service_name": "AmazonRDS",
            "specs_json": {
                "instance_type": "db.t3.medium",
                "avg_cpu_pct": 5.0,
            },
        },
        {
            "id": "res-3",
            "name": "orphan-ebs",
            "service_name": "AmazonEC2",
            "specs_json": {"status": "available"},
        },
    ]

    phase5_opportunities = [
        {
            "id": "opp-1",
            "resource_id": "res-3",
            "waste_type": "UNATTACHED_VOLUME",
            "estimated_waste_monthly": Decimal("3200.0000"),
        },
        {
            "id": "opp-2",
            "resource_id": "res-2",
            "waste_type": "IDLE_DATABASE",
            "estimated_waste_monthly": Decimal("6500.0000"),
        },
    ]

    report = EfficiencyAnalyzer.analyze(resources, phase5_opportunities)

    assert report.sufficiency_status == SufficiencyStatus.AVAILABLE
    assert len(report.headroom_items) == 2  # EC2 and RDS instances

    # Verify headrooms
    assert report.headroom_items[0].observed_utilization_headroom_cpu == Decimal("85.50")
    assert report.headroom_items[0].observed_utilization_headroom_memory == Decimal("72.00")

    # Verify waste decoupling: savings comes from explicit Phase 5 models (3200 + 6500 = 9700)
    assert report.idle_resources_count == 2
    assert report.idle_resources_cost == Decimal("9700.0000")
    assert report.estimated_addressable_waste == Decimal("9700.0000")

    # Verify unit economics are strictly NOT_CONFIGURED
    assert len(report.unit_economics) == 3
    for ue in report.unit_economics:
        assert ue.status == SufficiencyStatus.NOT_CONFIGURED
        assert ue.cost_per_unit is None
