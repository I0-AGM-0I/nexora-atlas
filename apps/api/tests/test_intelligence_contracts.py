"""
NEXORA ATLAS - Tests: Evidence Contracts
Verifies strict gating: if required operational telemetry is missing,
rules produce SKIPPED with explicit reasons, never hallucinated findings.
"""

import pytest
from decimal import Decimal
from app.intelligence.models import EvidenceContract
from app.intelligence.types import RuleStatus
from app.intelligence.waste.rules import (
    UnattachedVolumeRule,
    OversizedInstanceRule,
    OffHoursIdleRule,
    IdleDatabaseRule,
    LegacyStorageTierRule,
    UnassociatedEIPRule,
    UnmanagedObjectVersionsRule,
)


def test_evidence_contract_check_all_fields_present():
    contract = EvidenceContract(
        rule_name="TestContractRule",
        required_fields=["p95_cpu", "instance_type"],
        min_sample_size=1,
    )
    is_satisfied, reason = contract.check({"p95_cpu": 12.5, "instance_type": "m5.large"})
    assert is_satisfied is True
    assert reason is None


def test_evidence_contract_check_missing_field():
    contract = EvidenceContract(
        rule_name="TestContractRule",
        required_fields=["p95_cpu", "memory_mb"],
        min_sample_size=1,
    )
    is_satisfied, reason = contract.check({"p95_cpu": 12.5})
    assert is_satisfied is False
    assert "memory_mb" in reason


def test_evidence_contract_none_value_treated_as_missing():
    contract = EvidenceContract(
        rule_name="TestContractRule",
        required_fields=["days_unattached"],
        min_sample_size=1,
    )
    is_satisfied, reason = contract.check({"days_unattached": None})
    assert is_satisfied is False
    assert "days_unattached" in reason


def test_unattached_volume_rule_skipped_on_missing_telemetry():
    # Resource with missing days_unattached
    res = {
        "id": "res-vol-01",
        "account_id": "acc-01",
        "name": "vol-orphan",
        "native_id": "vol-12345",
        "specs_json": {"volume_status": "AVAILABLE"},  # missing days_unattached
    }
    eval_res, opp = UnattachedVolumeRule.evaluate(res, monthly_cost=Decimal("4500.00"), account_name="Dev Account")
    assert eval_res.status == RuleStatus.SKIPPED
    assert "days_unattached" in eval_res.skip_reason
    assert opp is None


def test_oversized_instance_rule_skipped_on_missing_p95_cpu():
    res = {
        "id": "res-ec2-01",
        "account_id": "acc-01",
        "name": "prod-worker",
        "native_id": "i-12345",
        "specs_json": {"instance_type": "m5.4xlarge"},  # missing p95_cpu_utilization_pct
    }
    eval_res, opp = OversizedInstanceRule.evaluate(res, monthly_cost=Decimal("49200.00"), account_name="Prod Account")
    assert eval_res.status == RuleStatus.SKIPPED
    assert "p95_cpu_utilization_pct" in eval_res.skip_reason
    assert opp is None



def test_idle_db_rule_skipped_on_empty_specs():
    res = {
        "id": "res-db-01",
        "account_id": "acc-01",
        "name": "staging-db",
        "native_id": "db-staging-1",
        "specs_json": {},
    }
    eval_res, opp = IdleDatabaseRule.evaluate(res, monthly_cost=Decimal("6300.00"), account_name="Staging Account")
    assert eval_res.status == RuleStatus.SKIPPED
    assert opp is None
