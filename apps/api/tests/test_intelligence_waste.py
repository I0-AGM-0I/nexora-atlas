"""
NEXORA ATLAS - Tests: Waste Detection Rules & Mathematical Precision
Verifies waste detection logic, operational contracts, and explicit assumptions dictionaries.
"""

from decimal import Decimal
from app.intelligence.types import WasteType, RuleStatus
from app.intelligence.waste.rules import (
    UnattachedVolumeRule,
    OversizedInstanceRule,
    OffHoursIdleRule,
    IdleDatabaseRule,
    LegacyStorageTierRule,
    UnassociatedEIPRule,
    UnmanagedObjectVersionsRule,
)
from app.intelligence.waste.calculators import (
    calculate_unattached_storage_waste,
    calculate_off_hours_idle_waste,
    calculate_gp3_migration_waste,
    calculate_rightsizing_waste,
)


def test_unattached_volume_detection_and_assumptions():
    res = {
        "id": "vol-1",
        "account_id": "acc-dev",
        "name": "orphaned-vol",
        "native_id": "vol-123456",
        "specs_json": {
            "volume_status": "AVAILABLE",
            "days_unattached": 18,
            "size_gb": 400,
            "volume_type": "gp2",
        },
    }
    eval_res, opp = UnattachedVolumeRule.evaluate(res, monthly_cost=Decimal("4500.00"), account_name="Dev Account")
    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert opp is not None
    assert opp.waste_type == WasteType.UNATTACHED_VOLUME
    assert opp.estimated_waste_monthly == Decimal("4500.0000")
    # Verify explicit assumptions dictionary
    assert "assumptions" in opp.evidence_json
    assert opp.evidence_json["assumptions"]["waste_factor"] == "1.00"
    assert len(opp.recommendations) == 1
    assert opp.recommendations[0].estimated_annual_savings == opp.recommendations[0].estimated_monthly_savings * Decimal("12")


def test_oversized_instance_multi_option_recommendations():
    res = {
        "id": "res-eks-node",
        "account_id": "acc-prod",
        "name": "analytics-worker-01",
        "native_id": "i-eks-01",
        "specs_json": {
            "instance_type": "m5.4xlarge",
            "p95_cpu_utilization_pct": 11.2,
            "cluster": "analytics-eks-cluster",
        },
    }
    eval_res, opp = OversizedInstanceRule.evaluate(res, monthly_cost=Decimal("49200.00"), account_name="Production")
    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert opp is not None
    # Must produce 2 candidate recommendations (Downsize + Graviton)
    assert len(opp.recommendations) == 2
    rec1 = opp.recommendations[0]
    rec2 = opp.recommendations[1]
    assert "m5.large" in rec1.title
    assert "Graviton" in rec2.title
    assert rec1.estimated_annual_savings == rec1.estimated_monthly_savings * Decimal("12")
    assert rec2.estimated_annual_savings == rec2.estimated_monthly_savings * Decimal("12")


def test_off_hours_idle_dev_compute():
    res = {
        "id": "res-dev-ec2",
        "account_id": "acc-dev",
        "name": "dev-sandbox-t3x-01",
        "native_id": "i-dev-01",
        "specs_json": {
            "instance_type": "t3.xlarge",
            "running_hours_per_week": 168,
            "observed_off_hours_cpu_pct": 0.8,
        },
    }
    eval_res, opp = OffHoursIdleRule.evaluate(res, monthly_cost=Decimal("12450.00"), account_name="Development")
    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert opp is not None
    assert opp.waste_type == WasteType.OFF_HOURS_IDLE
    # 75% savings on 12450 = 9337.5000
    assert opp.estimated_waste_monthly == Decimal("9337.5000")
    assert opp.evidence_json["assumptions"]["business_hours_per_month"] == "180"



def test_idle_database_detection():
    res = {
        "id": "res-dev-db",
        "account_id": "acc-dev",
        "name": "dev-db-01",
        "native_id": "db-dev-01",
        "specs_json": {
            "instance_class": "db.t3.small",
            "active_client_connections": 0,
            "idle_duration_pct": 88.5,
        },
    }
    eval_res, opp = IdleDatabaseRule.evaluate(res, monthly_cost=Decimal("6300.00"), account_name="Development")
    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert opp is not None
    assert opp.waste_type == WasteType.IDLE_DATABASE


def test_gp2_to_gp3_migration():
    res = {
        "id": "vol-gp2",
        "account_id": "acc-prod",
        "name": "analytics-legacy-storage",
        "native_id": "vol-gp2-01",
        "specs_json": {"volume_type": "gp2", "size_gb": 1000},
    }
    eval_res, opp = LegacyStorageTierRule.evaluate(res, monthly_cost=Decimal("10800.00"), account_name="Production")
    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert opp is not None
    # 20% savings on 10800 = 2160.0000
    assert opp.estimated_waste_monthly == Decimal("2160.0000")
    assert opp.recommendations[0].risk_level == "NONE"


def test_unassociated_eip_detection():
    res = {
        "id": "eip-1",
        "account_id": "acc-dev",
        "name": "idle-eip",
        "native_id": "eipalloc-01",
        "specs_json": {
            "association_status": "UNATTACHED",
            "idle_duration_days": 28,
        },
    }
    eval_res, opp = UnassociatedEIPRule.evaluate(res, monthly_cost=Decimal("1050.00"), account_name="Development")
    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert opp is not None
    assert opp.waste_type == WasteType.UNASSOCIATED_EIP
    assert opp.estimated_waste_monthly == Decimal("1050.0000")


def test_unmanaged_object_versions_detection():
    res = {
        "id": "bucket-1",
        "account_id": "acc-prod",
        "name": "nexora-raw-data-lake",
        "native_id": "nexora-raw-data-lake",
        "specs_json": {
            "non_current_versions_gb": 18400,
            "lifecycle_rules_found": 0,
        },
    }
    eval_res, opp = UnmanagedObjectVersionsRule.evaluate(res, monthly_cost=Decimal("58500.00"), account_name="Production")
    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert opp is not None
    assert opp.waste_type == WasteType.UNMANAGED_OBJECT_VERSIONS
