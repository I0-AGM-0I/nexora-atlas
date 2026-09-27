"""
NEXORA ATLAS - Phase 9 Milestone 2: Freshness Evaluation Test Suite
Verifies source-specific freshness calculation from actual timestamps without fabrication.
"""

import pytest
from datetime import datetime, timezone, timedelta, date

from app.ai.types import DataFreshnessStatus, EpistemicClass
from app.ai.models import EvidenceItem
from app.ai.retrieval.freshness import (
    evaluate_timestamp_freshness,
    evaluate_package_freshness,
    attach_evidence_item_freshness,
    CLOUDWATCH_FRESH_HOURS,
    RESOURCE_SYNC_FRESH_HOURS,
)


def test_evaluate_fresh_timestamp():
    """Recent timestamp within threshold is FRESH."""
    now = datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)
    recent_ts = now - timedelta(hours=1)

    status = evaluate_timestamp_freshness(recent_ts, threshold_hours=4, now=now)
    assert status == DataFreshnessStatus.FRESH


def test_evaluate_stale_timestamp():
    """Old timestamp exceeding threshold is STALE."""
    now = datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)
    stale_ts = now - timedelta(hours=6)

    status = evaluate_timestamp_freshness(stale_ts, threshold_hours=4, now=now)
    assert status == DataFreshnessStatus.STALE


def test_evaluate_missing_timestamp_is_unknown():
    """Missing (None) timestamp returns UNKNOWN without fabricating timestamps."""
    status = evaluate_timestamp_freshness(None, threshold_hours=4)
    assert status == DataFreshnessStatus.UNKNOWN


def test_package_freshness_evaluation():
    """Evaluates multi-source package freshness."""
    now = datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)
    recent_cw = now - timedelta(minutes=45)
    recent_cost_date = date(2026, 9, 25)

    freshness = evaluate_package_freshness(
        cost_date=recent_cost_date,
        cw_retrieved_at=recent_cw,
        now=now,
    )
    assert freshness.status == DataFreshnessStatus.FRESH
    assert "45 minutes ago" in freshness.freshness_summary
    assert "2026-09-25" in freshness.cost_data_through


def test_package_freshness_stale_detection():
    """Stale cost data marks package as STALE."""
    now = datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)
    old_cost_date = date(2026, 8, 15)  # 40+ days old

    freshness = evaluate_package_freshness(
        cost_date=old_cost_date,
        cw_retrieved_at=now - timedelta(hours=10),
        now=now,
    )
    assert freshness.status == DataFreshnessStatus.STALE


def test_evidence_item_level_freshness():
    """Attaches per-item freshness status into evidence item metadata."""
    item = EvidenceItem(
        id="ev-cw-test",
        type="TELEMETRY",
        epistemic_class=EpistemicClass.OBSERVED,
        statement="Test observation",
    )
    ts = datetime.now(timezone.utc) - timedelta(minutes=30)
    enriched = attach_evidence_item_freshness(item, observed_at=ts, threshold_hours=2)

    assert enriched.metadata["freshness"] == DataFreshnessStatus.FRESH.value
    assert "observed_at" in enriched.metadata
