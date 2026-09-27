"""
NEXORA ATLAS - Tests: Anomaly Detection Rules
Verifies Rules A, B, C, D, MAD handling, population gating, and severity scoring.
"""

from decimal import Decimal
from datetime import date, timedelta
from app.intelligence.types import Severity, RuleStatus, AnomalyRuleType
from app.intelligence.anomaly.rules import (
    CostSpikeRule,
    SustainedIncreaseRule,
    ResourceOutlierRule,
    AccountShiftRule,
)
from app.intelligence.anomaly.scoring import calculate_anomaly_severity


def test_rule_a_cost_spike_detection():
    # 14 days of baseline ~100/day, followed by a spike to 250 (+150%)
    base_date = date(2026, 1, 1)
    series = [(base_date + timedelta(days=i), Decimal("100.00")) for i in range(14)]
    series.append((base_date + timedelta(days=14), Decimal("250.00")))

    eval_res, finding = CostSpikeRule.evaluate(
        account_id="acc-prod",
        account_name="Production",
        service_name="AmazonEC2",
        series=series,
        resource_id="res-gpu-01",
        resource_name="gpu-training-node",
        environment="production",
    )

    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert finding is not None
    assert finding.anomaly_type == AnomalyRuleType.COST_SPIKE
    assert finding.detected_spend == Decimal("250.0000")
    assert finding.expected_spend == Decimal("100.0000")
    assert finding.percentage_deviation == Decimal("150.00")
    assert finding.severity in (Severity.HIGH, Severity.CRITICAL)


def test_rule_a_clean_when_within_normal_variance():
    base_date = date(2026, 1, 1)
    series = [(base_date + timedelta(days=i), Decimal("100.00") + Decimal(str(i % 3))) for i in range(15)]

    eval_res, finding = CostSpikeRule.evaluate(
        account_id="acc-prod",
        account_name="Production",
        service_name="AmazonEC2",
        series=series,
        resource_id="res-web-01",
    )
    assert eval_res.status == RuleStatus.EVALUATED_CLEAN
    assert finding is None


def test_rule_b_sustained_increase():
    # 14 days of 100/day, followed by 4 days of 130/day (+30%)
    base_date = date(2026, 1, 1)
    series = [(base_date + timedelta(days=i), Decimal("100.00")) for i in range(14)]
    for i in range(4):
        series.append((base_date + timedelta(days=14 + i), Decimal("130.00")))

    eval_res, finding = SustainedIncreaseRule.evaluate(
        account_id="acc-prod",
        account_name="Production",
        service_name="AmazonRDS",
        series=series,
        resource_id="res-db-01",
        environment="production",
    )

    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert finding is not None
    assert finding.anomaly_type == AnomalyRuleType.SUSTAINED_INCREASE
    assert finding.duration_days >= 3


def test_rule_c_outlier_population_gating():
    # Cohort of only 2 resources (min population is 4)
    resources = [
        {"resource_id": "r1", "name": "res-1", "period_cost": Decimal("1000.00"), "environment": "production"},
        {"resource_id": "r2", "name": "res-2", "period_cost": Decimal("9000.00"), "environment": "production"},
    ]
    eval_res, findings = ResourceOutlierRule.evaluate(
        account_id="acc-1",
        account_name="Production",
        service_name="AmazonEC2",
        resource_items=resources,
    )
    assert eval_res.status == RuleStatus.SKIPPED
    assert "population too small" in eval_res.skip_reason.lower()
    assert len(findings) == 0


def test_rule_c_outlier_with_zero_mad():
    # 5 resources, 4 identical at 1000, 1 outlier at 5000 (MAD = 0)
    resources = [
        {"resource_id": f"r{i}", "name": f"worker-{i}", "period_cost": Decimal("1000.00"), "environment": "production"}
        for i in range(1, 5)
    ]
    resources.append({"resource_id": "r5", "name": "worker-heavy", "period_cost": Decimal("5000.00"), "environment": "production"})

    eval_res, findings = ResourceOutlierRule.evaluate(
        account_id="acc-1",
        account_name="Production",
        service_name="AmazonEC2",
        resource_items=resources,
    )
    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert len(findings) == 1
    assert findings[0].resource_id == "r5"
    assert findings[0].detected_spend == Decimal("5000.00")


def test_rule_d_account_shift():
    # Org spend: 100,000 prev, 120,000 current
    # Account spend: 20,000 prev (20%), 40,000 current (33.3%) -> share delta ~13.3% > 10%
    eval_res, finding = AccountShiftRule.evaluate(
        account_id="acc-dev",
        account_name="Development Account",
        current_spend=Decimal("40000.00"),
        prev_spend=Decimal("20000.00"),
        org_current_spend=Decimal("120000.00"),
        org_prev_spend=Decimal("100000.00"),
        environment="development",
    )
    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert finding is not None
    assert finding.anomaly_type == AnomalyRuleType.ACCOUNT_SHIFT


def test_severity_scoring_environment_multiplier():
    # Same INR amount and deviation, but production vs development
    sev_prod = calculate_anomaly_severity(
        magnitude_inr=Decimal("25000.00"),
        percentage_change=Decimal("40.0"),
        duration_days=1,
        environment="production",
    )
    sev_dev = calculate_anomaly_severity(
        magnitude_inr=Decimal("25000.00"),
        percentage_change=Decimal("40.0"),
        duration_days=1,
        environment="development",
    )
    # Production should be equal or higher severity due to 1.3x multiplier
    severity_rank = {Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3, Severity.CRITICAL: 4}
    assert severity_rank[sev_prod] >= severity_rank[sev_dev]

