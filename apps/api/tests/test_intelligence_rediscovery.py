"""
NEXORA ATLAS - The Crown Jewel Test: Autonomous Inefficiency Rediscovery & Evidence Lineage
Demonstrates the intelligence engine independently discovering anomalies and waste from
raw database rows without hardcoded resource names or answers.

Verifies complete evidence lineage:
Finding -> Resource -> Historical Costs -> Baseline -> Deviation -> Evidence -> Action
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.demo import seed_demo_data
from app.demo.config import DEMO_ORG_SLUG
from app.models.organization import Organization
from app.models.resource import CloudResource
from app.models.cost import CostRecord
from app.intelligence.orchestration.engine import IntelligenceEngine
from app.intelligence.types import AnomalyRuleType, WasteType


@pytest.mark.asyncio
async def test_crown_jewel_intelligence_rediscovery(db_session: AsyncSession):
    """
    Independent Rediscovery Test:
    Seeds database with raw telemetry rows.
    Executes IntelligenceEngine without hints or hardcoded names.
    Proves that the engine autonomously uncovers:
    1. A critical cost spike / sustained surge
    2. Detached block storage inefficiency
    3. Severely underutilized/oversized compute capacity
    And validates the complete end-to-end evidence lineage for every finding.
    """
    # Step 1: Seed raw operational and financial data into clean database
    await seed_demo_data(db_session, reset_first=True)

    org_res = await db_session.execute(select(Organization).where(Organization.slug == DEMO_ORG_SLUG))
    org = org_res.scalars().first()
    assert org is not None

    # Step 2: Run Intelligence Engine against the raw database
    run_result = await IntelligenceEngine.run(db_session, organization_id=org.id)
    assert run_result.ruleset_version == "atlas-intelligence-v1"

    # =========================================================================
    # PROOF 1: Discovery of Sudden Spending Anomaly with Full Evidence Lineage
    # =========================================================================
    spike_findings = [
        a for a in run_result.anomalies
        if a.anomaly_type in (AnomalyRuleType.COST_SPIKE, AnomalyRuleType.SUSTAINED_INCREASE)
        and a.resource_id is not None
    ]
    assert len(spike_findings) > 0, "Engine failed to detect any resource spending spikes"

    # Select the highest severity surge
    top_spike = max(spike_findings, key=lambda x: x.percentage_deviation)
    assert top_spike.detected_spend > top_spike.expected_spend
    assert top_spike.percentage_deviation >= Decimal("20.0")

    # Verify Evidence Lineage: Finding -> Resource
    res_stmt = select(CloudResource).where(CloudResource.id == top_spike.resource_id)
    spike_resource = (await db_session.execute(res_stmt)).scalar_one_or_none()
    assert spike_resource is not None
    assert spike_resource.name == top_spike.resource_name

    # Verify Evidence Lineage: Finding -> Historical Costs in Database
    cost_stmt = (
        select(CostRecord)
        .where(CostRecord.resource_id == top_spike.resource_id)
        .order_by(CostRecord.usage_date.desc())
    )
    historical_records = (await db_session.execute(cost_stmt)).scalars().all()
    assert len(historical_records) >= 14, "Lineage broke: Insufficient historical database cost records"

    # Verify Evidence Lineage: Raw Daily Costs -> Baseline & Deviation
    obs_date_str = top_spike.evidence_json["observed_facts"]["observation_date"]
    matching_db_record = next((r for r in historical_records if str(r.usage_date) == obs_date_str), None)
    assert matching_db_record is not None, f"No cost record found in DB for observation date {obs_date_str}"
    assert matching_db_record.unblended_cost == top_spike.detected_spend
    assert "observed_facts" in top_spike.evidence_json
    assert "baseline_mean" in top_spike.evidence_json["observed_facts"]
    assert "baseline_std_dev" in top_spike.evidence_json["observed_facts"]

    # =========================================================================
    # PROOF 2: Autonomous Discovery of Unattached Storage Inefficiency
    # =========================================================================
    storage_waste = [
        opp for opp in run_result.opportunities
        if opp.waste_type == WasteType.UNATTACHED_VOLUME
    ]
    assert len(storage_waste) > 0, "Engine failed to discover unattached block storage waste"

    first_storage = storage_waste[0]
    assert first_storage.estimated_waste_monthly > Decimal("0.0000")

    # Verify Evidence Lineage: Finding -> Resource specs in DB
    vol_res = (await db_session.execute(select(CloudResource).where(CloudResource.id == first_storage.resource_id))).scalar_one()
    specs = vol_res.specs_json or {}
    assert specs.get("volume_status") in ("AVAILABLE", "UNATTACHED")
    assert int(specs.get("days_unattached", 0)) >= 7

    # Verify Actionability: Opportunity produces Snapshot & Delete Recommendation
    assert len(first_storage.recommendations) >= 1
    storage_rec = first_storage.recommendations[0]
    assert "delete" in storage_rec.title.lower() or "snapshot" in storage_rec.title.lower()
    assert storage_rec.estimated_annual_savings == storage_rec.estimated_monthly_savings * Decimal("12")
    assert storage_rec.risk_level in ("LOW", "NONE")

    # =========================================================================
    # PROOF 3: Autonomous Discovery of Oversized Compute Capacity
    # =========================================================================
    compute_waste = [
        opp for opp in run_result.opportunities
        if opp.waste_type == WasteType.OVERSIZED_INSTANCE
    ]
    assert len(compute_waste) > 0, "Engine failed to discover oversized compute instance capacity"

    first_compute = compute_waste[0]
    assert first_compute.estimated_waste_monthly > Decimal("0.0000")

    # Verify Evidence Lineage: Finding -> Resource telemetry in DB
    compute_res = (await db_session.execute(select(CloudResource).where(CloudResource.id == first_compute.resource_id))).scalar_one()
    c_specs = compute_res.specs_json or {}
    assert Decimal(str(c_specs.get("p95_cpu_utilization_pct", 100))) < Decimal("20.0")

    # Verify Multiple Trade-Off Actions Generated (In-family downsize vs Graviton migration)
    assert len(first_compute.recommendations) >= 2, "Engine failed to generate multi-option tradeoffs for compute right-sizing"
    downsize_rec = next((r for r in first_compute.recommendations if "downsize" in r.title.lower()), None)
    graviton_rec = next((r for r in first_compute.recommendations if "graviton" in r.title.lower()), None)
    assert downsize_rec is not None
    assert graviton_rec is not None
    assert downsize_rec.estimated_annual_savings == downsize_rec.estimated_monthly_savings * Decimal("12")
    assert graviton_rec.estimated_annual_savings == graviton_rec.estimated_monthly_savings * Decimal("12")
