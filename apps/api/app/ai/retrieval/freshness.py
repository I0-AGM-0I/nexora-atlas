"""
NEXORA ATLAS - Freshness Evaluation (Phase 9)
Evaluates real data observation timestamps against source-specific SLAs.

CRITICAL INVARIANT:
  Freshness is calculated from real timestamps; never fabricated.
  Distinguishes fresh, stale, and unknown states at the evidence item level
  as well as the package level.
"""

from datetime import datetime, timezone, timedelta, date
from typing import Optional, Dict, Any, List
from app.ai.types import DataFreshnessStatus
from app.ai.models import DataFreshness, EvidenceItem

# Source-specific freshness thresholds
BILLING_FRESH_HOURS = 48         # AWS Cost Explorer finalized data is typically 24-48h behind
CLOUDWATCH_FRESH_HOURS = 4       # CloudWatch metrics within 4h are considered FRESH
RESOURCE_SYNC_FRESH_HOURS = 24   # Resource inventory within 24h is FRESH
RECOMMENDATION_FRESH_HOURS = 72  # Optimization opportunities re-evaluated every 72h


def evaluate_timestamp_freshness(
    ts: Optional[datetime],
    threshold_hours: int,
    now: Optional[datetime] = None,
) -> DataFreshnessStatus:
    """Evaluates whether a specific observation timestamp is FRESH, STALE, or UNKNOWN."""
    if ts is None:
        return DataFreshnessStatus.UNKNOWN

    current_time = now or datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    age = current_time - ts
    if age < timedelta(0):
        # Timestamp in the future or clock skew -> treat as FRESH
        return DataFreshnessStatus.FRESH

    if age <= timedelta(hours=threshold_hours):
        return DataFreshnessStatus.FRESH
    return DataFreshnessStatus.STALE


def evaluate_package_freshness(
    cost_date: Optional[date] = None,
    cw_retrieved_at: Optional[datetime] = None,
    resource_synced_at: Optional[datetime] = None,
    now: Optional[datetime] = None,
) -> DataFreshness:
    """
    Computes evidence package freshness from underlying source observation timestamps.
    """
    current_time = now or datetime.now(timezone.utc)

    cw_status = evaluate_timestamp_freshness(cw_retrieved_at, CLOUDWATCH_FRESH_HOURS, current_time)
    res_status = evaluate_timestamp_freshness(resource_synced_at, RESOURCE_SYNC_FRESH_HOURS, current_time)

    # Cost date freshness check (date vs today)
    cost_status = DataFreshnessStatus.UNKNOWN
    cost_str = "No cost data"
    if cost_date:
        cost_str = str(cost_date)
        today = current_time.date()
        days_old = (today - cost_date).days
        if days_old <= 2:
            cost_status = DataFreshnessStatus.FRESH
        else:
            cost_status = DataFreshnessStatus.STALE

    # Telemetry age label
    cw_age_str = "No telemetry recorded"
    if cw_retrieved_at:
        if cw_retrieved_at.tzinfo is None:
            cw_retrieved_at = cw_retrieved_at.replace(tzinfo=timezone.utc)
        mins = max(0, int((current_time - cw_retrieved_at).total_seconds() / 60))
        cw_age_str = f"{mins} minutes ago" if mins < 120 else f"{mins // 60} hours ago"

    # Overall package freshness evaluation
    if cost_status == DataFreshnessStatus.FRESH and cw_status in [DataFreshnessStatus.FRESH, DataFreshnessStatus.UNKNOWN]:
        overall_status = DataFreshnessStatus.FRESH
    elif cost_status == DataFreshnessStatus.STALE or cw_status == DataFreshnessStatus.STALE:
        overall_status = DataFreshnessStatus.STALE
    else:
        overall_status = DataFreshnessStatus.UNKNOWN

    summary = f"Cost data through: {cost_str}. CloudWatch telemetry retrieved: {cw_age_str}."

    return DataFreshness(
        cloudwatch_retrieved_at=cw_retrieved_at,
        cost_data_through=cost_str,
        resource_inventory_synced_at=resource_synced_at,
        status=overall_status,
        freshness_summary=summary,
    )


def attach_evidence_item_freshness(
    item: EvidenceItem,
    observed_at: Optional[datetime] = None,
    threshold_hours: int = 24,
) -> EvidenceItem:
    """Attaches per-item freshness status into evidence item metadata."""
    status = evaluate_timestamp_freshness(observed_at, threshold_hours)
    new_metadata = dict(item.metadata)
    new_metadata["freshness"] = status.value
    if observed_at:
        new_metadata["observed_at"] = observed_at.isoformat()

    # Reconstruct frozen EvidenceItem with enriched metadata
    return EvidenceItem(
        id=item.id,
        type=item.type,
        epistemic_class=item.epistemic_class,
        statement=item.statement,
        value=item.value,
        unit=item.unit,
        source=item.source,
        source_entity_id=item.source_entity_id,
        confidence=item.confidence,
        period_or_timestamp=item.period_or_timestamp,
        metadata=new_metadata,
    )
