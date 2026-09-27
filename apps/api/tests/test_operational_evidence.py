"""
NEXORA ATLAS - Phase 8 Operational Evidence & Telemetry Gating Tests
Verifies that:
1. Operational telemetry is strictly required by evidence contracts.
2. Missing telemetry is never imputed as zero.
3. Coverage thresholds (< 70%) gate rightsizing evaluation.
4. Multi-dimensional compute metrics (CPU + Memory) guard against false positive rightsizing.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app.intelligence.constants import (
    MIN_TELEMETRY_COVERAGE_FOR_RIGHTSIZING,
    HIGH_MEMORY_CONSTRAINED_THRESHOLD_PCT,
)
from app.intelligence.types import RuleStatus, WasteType
from app.intelligence.waste.rules import OversizedInstanceRule, IdleDatabaseRule
from app.integrations.providers.aws.telemetry.processor import TelemetryStatisticalProcessor
from app.analytics.types import SufficiencyStatus


def test_missing_telemetry_produces_not_configured_never_zero():
    """Missing observations must evaluate to NOT_CONFIGURED, never zero."""
    now = datetime.now(timezone.utc)
    stats = TelemetryStatisticalProcessor.process_series(
        metric_name="CPUUtilization",
        unit="Percent",
        observations=[],
        window_start=now - timedelta(days=30),
        window_end=now,
        period_seconds=300,
        now=now,
    )
    assert stats.sufficiency_status == SufficiencyStatus.NOT_CONFIGURED
    assert stats.p95 is None
    assert stats.mean is None
    assert stats.sample_count == 0
    assert stats.coverage_ratio == Decimal("0.00")


def test_telemetry_coverage_gating_blocks_insufficient_data():
    """Resources with under 70% telemetry coverage must be SKIPPED for rightsizing."""
    resource = {
        "id": "res-ec2-low-cov",
        "account_id": "acc-prod",
        "name": "api-worker-sparse",
        "native_id": "i-sparse-01",
        "specs_json": {
            "instance_type": "m5.2xlarge",
            "p95_cpu_utilization_pct": 12.0,
            "telemetry_coverage_ratio": Decimal("0.45"),  # 45% coverage < 70% required
        },
    }

    eval_res, opp = OversizedInstanceRule.evaluate(
        resource=resource,
        monthly_cost=Decimal("25000.0000"),
        account_name="Production",
    )

    assert eval_res.status == RuleStatus.SKIPPED
    assert "Insufficient telemetry coverage" in eval_res.skip_reason
    assert "45.0%" in eval_res.skip_reason
    assert opp is None


def test_high_memory_constraint_prevents_downsizing():
    """Golden Scenario 5 (Resource E): Low CPU (8%) + High Memory (92%) must NOT be downsized."""
    resource = {
        "id": "res-ec2-high-mem",
        "account_id": "acc-prod",
        "name": "memcached-node-01",
        "native_id": "i-mem-01",
        "specs_json": {
            "instance_type": "m5.4xlarge",
            "p95_cpu_utilization_pct": 8.0,
            "p95_memory_utilization_pct": 92.0,  # 92% >= 80% threshold
            "telemetry_coverage_ratio": Decimal("0.95"),
        },
    }

    eval_res, opp = OversizedInstanceRule.evaluate(
        resource=resource,
        monthly_cost=Decimal("45000.0000"),
        account_name="Production",
    )

    assert eval_res.status == RuleStatus.SKIPPED
    assert "High memory constraint" in eval_res.skip_reason
    assert opp is None


def test_missing_memory_telemetry_discounts_confidence():
    """When CPU is low and coverage is high, but Memory is NOT_CONFIGURED, rightsizing confidence is discounted."""
    resource = {
        "id": "res-ec2-no-mem",
        "account_id": "acc-prod",
        "name": "batch-processor-01",
        "native_id": "i-batch-01",
        "specs_json": {
            "instance_type": "m5.2xlarge",
            "p95_cpu_utilization_pct": 14.5,
            "memory_sufficiency": "NOT_CONFIGURED",
            "telemetry_coverage_ratio": Decimal("0.90"),
        },
    }

    eval_res, opp = OversizedInstanceRule.evaluate(
        resource=resource,
        monthly_cost=Decimal("28000.0000"),
        account_name="Production",
    )

    assert eval_res.status == RuleStatus.EVALUATED_VIOLATION
    assert opp is not None
    # Discounted confidence (80.00 instead of 94.00)
    assert opp.confidence_score == Decimal("80.00")
    assert opp.recommendations[0].confidence_score == Decimal("80.00")
    assert "Memory telemetry not configured" in opp.recommendations[0].reasoning
    assert opp.recommendations[0].risk_level == "MEDIUM"
