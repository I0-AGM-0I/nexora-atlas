"""
NEXORA ATLAS - Phase 8 Production Intelligence Tests
Verifies Multi-AZ database preservation, epistemic rightsizing recommendations,
and Phase 6 cost driver attribution with LIKELY_USAGE_DRIVEN operational contracts.
"""

import pytest
from decimal import Decimal

from app.intelligence.types import RuleStatus, WasteType
from app.intelligence.waste.rules import OversizedInstanceRule, IdleDatabaseRule
from app.analytics.types import ChangeClassification, DriverDimension
from app.analytics.drivers.ranking import classify_resource_change
from app.analytics.efficiency.metrics import extract_resource_headroom


def test_multiaz_database_preservation():
    """Multi-AZ production databases must NEVER be decommissioned due to low activity."""
    multi_az_resource = {
        "id": "res-rds-ha",
        "account_id": "acc-prod",
        "name": "prod-aurora-primary",
        "native_id": "db-prod-cluster-1",
        "specs_json": {
            "instance_class": "db.r5.xlarge",
            "active_client_connections": 0,
            "idle_duration_pct": 99.0,
            "multi_az": True,  # High-Availability architecture
        },
    }

    eval_res, opp = IdleDatabaseRule.evaluate(
        resource=multi_az_resource,
        monthly_cost=Decimal("75000.0000"),
        account_name="Production",
    )

    assert eval_res.status == RuleStatus.SKIPPED
    assert "Multi-AZ redundancy indicates high-availability production database" in eval_res.skip_reason
    assert opp is None


def test_single_az_low_activity_database_evaluation():
    """Single-AZ dev database with low activity produces an evaluation opportunity without claiming deletion authority."""
    single_az_resource = {
        "id": "res-rds-dev",
        "account_id": "acc-dev",
        "name": "dev-reporting-db",
        "native_id": "db-dev-01",
        "specs_json": {
            "instance_class": "db.t3.small",
            "active_client_connections": 0,
            "idle_duration_pct": 85.0,
            "multi_az": False,
        },
    }

    eval_res, opp = IdleDatabaseRule.evaluate(
        resource=single_az_resource,
        monthly_cost=Decimal("5400.0000"),
        account_name="Development",
    )

    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert opp is not None
    assert opp.waste_type == WasteType.IDLE_DATABASE
    assert len(opp.recommendations) == 1
    rec = opp.recommendations[0]
    assert rec.title == "Evaluate Low Activity Database"
    assert rec.assumptions_json.get("autonomous_authority") is False
    assert "Evidence warrants operational review" in rec.reasoning


def test_likely_usage_driven_cost_classification():
    """Validates the Phase 8 LIKELY_USAGE_DRIVEN formal contract: aligned windows + cost delta >= 5% + coverage >= 70% + op delta >= 5%."""
    classification = classify_resource_change(
        current_cost=Decimal("35000.0000"),
        previous_cost=Decimal("25000.0000"),  # +40% cost increase
        current_spec="m5.2xlarge",
        previous_spec="m5.2xlarge",
        usage_telemetry={
            "telemetry_coverage_ratio": Decimal("0.95"),
            "operational_delta_pct": Decimal("38.5"),
        },
    )
    assert classification == ChangeClassification.LIKELY_USAGE_DRIVEN


def test_usage_classification_fallback_on_low_coverage():
    """If coverage is under 70%, LIKELY_USAGE_DRIVEN is not granted; falls back to general USAGE if volume changed."""
    classification = classify_resource_change(
        current_cost=Decimal("35000.0000"),
        previous_cost=Decimal("25000.0000"),
        current_spec="m5.2xlarge",
        previous_spec="m5.2xlarge",
        usage_telemetry={
            "telemetry_coverage_ratio": Decimal("0.50"),  # < 70%
            "operational_delta_pct": Decimal("38.5"),
        },
    )
    # LIKELY_USAGE_DRIVEN contract failed due to coverage, but general USAGE applies
    assert classification == ChangeClassification.USAGE


def test_capacity_headroom_extraction_from_real_telemetry():
    """Efficiency analyzer headroom extracts p95 utilization directly from specs_json enriched by CloudWatch."""
    specs = {
        "instance_type": "m5.4xlarge",
        "p95_cpu_utilization_pct": Decimal("18.4"),
        "p95_memory_utilization_pct": Decimal("42.0"),
    }
    item = extract_resource_headroom(
        resource_id="res-101",
        resource_name="prod-frontend-01",
        service_name="AmazonEC2",
        specs=specs,
    )

    assert item.p95_utilization_cpu == Decimal("18.40")
    assert item.p95_utilization_memory == Decimal("42.00")
    # Headroom = 100 - p95
    assert item.observed_utilization_headroom_cpu == Decimal("81.60")
    assert item.observed_utilization_headroom_memory == Decimal("58.00")
