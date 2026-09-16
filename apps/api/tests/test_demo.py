"""
NEXORA ATLAS - Demo Data Engine Tests (Phase 3)
Verifies:
- Deterministic seeding and reproducibility
- Idempotency
- Mathematical financial reconciliation
- Anomaly calculation and observed vs inferred separation
- Opportunity and recommendation math
- Scenario delta math
- Safe scoped reset (demo orgs only, preserving production orgs)
- Demo API endpoints (/status, /seed, /reset)
- DEMO_MODE security guardrail
- Zero AWS network/SDK calls
"""

from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import (
    Organization,
    CloudAccount,
    CloudResource,
    CostRecord,
    CostSnapshot,
    Anomaly,
    OptimizationOpportunity,
    Recommendation,
    Scenario,
    Forecast,
)
from app.demo import (
    seed_demo_data,
    reset_demo_data,
    validate_demo_dataset,
    format_health_report_text,
)
from app.demo.config import DEMO_ORG_SLUG, DEMO_ORG_NAME


@pytest.mark.asyncio
async def test_demo_seed_and_validation(db_session: AsyncSession):
    """Verifies that seed_demo_data populates the entire environment and validation passes."""
    seed_result = await seed_demo_data(db_session, reset_first=True)
    assert seed_result["status"] == "seeded"
    assert seed_result["organization"] == DEMO_ORG_NAME

    report = await validate_demo_dataset(db_session)
    assert report["organization"] == DEMO_ORG_NAME
    assert report["accounts"] == 3
    assert report["resources"] == 58
    assert report["cost_records"] == 5220
    assert report["anomalies"] == 4
    assert report["optimization_opportunities"] >= 6
    assert report["recommendations"] >= 6
    assert report["scenarios"] == 3
    assert report["forecasts"] == 3
    assert report["financial_reconciliation"] == "PASS"
    assert report["tenant_integrity"] == "PASS"
    assert report["relationship_integrity"] == "PASS"
    assert report["tag_uniqueness"] == "PASS"
    assert report["aws_network_calls"] == 0

    # Ensure ASCII health report generation succeeds without errors
    text_report = format_health_report_text(report)
    assert "NEXORA ATLAS DEMO DATA HEALTH" in text_report
    assert "Financial reconciliation: PASS" in text_report


@pytest.mark.asyncio
async def test_demo_seed_determinism(db_session: AsyncSession):
    """Verifies that running seed, reset, and re-seed produces bit-for-bit identical aggregate metrics."""
    # First seed
    await seed_demo_data(db_session, reset_first=True)

    sum_1_res = await db_session.execute(select(func.sum(CostRecord.unblended_cost)))
    total_spend_1 = sum_1_res.scalar()

    count_1_res = await db_session.execute(select(func.count(CostRecord.id)))
    count_1 = count_1_res.scalar()

    anom_1_res = await db_session.execute(
        select(Anomaly.observed_cost, Anomaly.baseline_cost).order_by(Anomaly.detected_at)
    )
    anomalies_1 = anom_1_res.all()

    # Second seed (wiping and re-seeding with fixed seed 424242)
    await seed_demo_data(db_session, reset_first=True)

    sum_2_res = await db_session.execute(select(func.sum(CostRecord.unblended_cost)))
    total_spend_2 = sum_2_res.scalar()

    count_2_res = await db_session.execute(select(func.count(CostRecord.id)))
    count_2 = count_2_res.scalar()

    anom_2_res = await db_session.execute(
        select(Anomaly.observed_cost, Anomaly.baseline_cost).order_by(Anomaly.detected_at)
    )
    anomalies_2 = anom_2_res.all()

    # Assert 100% deterministic reproducibility
    assert count_1 == count_2 == 5220
    assert total_spend_1 == total_spend_2
    assert len(anomalies_1) == len(anomalies_2) == 4
    for a1, a2 in zip(anomalies_1, anomalies_2):
        assert a1[0] == a2[0]  # observed_cost identical
        assert a1[1] == a2[1]  # baseline_cost identical


@pytest.mark.asyncio
async def test_demo_seed_idempotency(db_session: AsyncSession):
    """Verifies that calling seed twice without reset_first returns already_seeded without duplicating rows."""
    res1 = await seed_demo_data(db_session, reset_first=True)
    assert res1["status"] == "seeded"

    count1 = (await db_session.execute(select(func.count(CostRecord.id)))).scalar()

    # Second call without reset
    res2 = await seed_demo_data(db_session, reset_first=False)
    assert res2["status"] == "already_seeded"

    count2 = (await db_session.execute(select(func.count(CostRecord.id)))).scalar()
    assert count1 == count2 == 5220


@pytest.mark.asyncio
async def test_financial_reconciliation_exact(db_session: AsyncSession):
    """
    Verifies mathematical financial reconciliation:
    1. Sum of CostRecord.unblended_cost == Sum of monthly CostSnapshot.total_cost
    2. Recommendation annual_savings == monthly_savings * 12
    3. Scenario monthly_savings == baseline - projected
    """
    await seed_demo_data(db_session, reset_first=True)

    # 1. CostRecord sum vs Monthly CostSnapshot sum
    record_sum = (await db_session.execute(select(func.sum(CostRecord.unblended_cost)))).scalar()
    snapshot_sum = (await db_session.execute(
        select(func.sum(CostSnapshot.total_cost)).where(CostSnapshot.period_type == "MONTHLY")
    )).scalar()

    assert record_sum == snapshot_sum, f"Record sum ({record_sum}) != Snapshot sum ({snapshot_sum})"

    # 2. Recommendations annual == monthly * 12
    recs = (await db_session.execute(select(Recommendation))).scalars().all()
    assert len(recs) > 0
    for rec in recs:
        assert rec.estimated_annual_savings == rec.estimated_monthly_savings * 12

    # 3. Scenarios delta
    scenarios = (await db_session.execute(select(Scenario))).scalars().all()
    assert len(scenarios) == 3
    for sc in scenarios:
        expected_savings = sc.baseline_monthly_cost - sc.projected_monthly_cost
        assert sc.monthly_savings == expected_savings
        expected_pct = round((expected_savings / sc.baseline_monthly_cost) * 100, 2)
        assert round(sc.percentage_savings, 2) == expected_pct


@pytest.mark.asyncio
async def test_anomaly_calculations_and_separation(db_session: AsyncSession):
    """
    Verifies that all anomalies:
    - Have positive observed and baseline costs
    - Percentage change strictly matches ((observed - baseline) / baseline) * 100
    - Observed vs inferred fields are separated
    """
    await seed_demo_data(db_session, reset_first=True)

    anomalies = (await db_session.execute(select(Anomaly))).scalars().all()
    assert len(anomalies) == 4

    for anom in anomalies:
        assert anom.observed_cost > Decimal("0.0000")
        assert anom.baseline_cost > Decimal("0.0000")
        expected_change = round(((anom.observed_cost - anom.baseline_cost) / anom.baseline_cost) * 100, 2)
        assert round(anom.percentage_change, 2) == expected_change
        # Inferred root cause and explanation exist
        assert anom.inferred_cause is not None
        assert isinstance(anom.inference_details_json, dict)
        assert len(anom.inference_details_json) > 0


@pytest.mark.asyncio
async def test_safe_scoped_reset(db_session: AsyncSession):
    """
    Verifies that reset_demo_data ONLY deletes is_demo=True organizations,
    leaving any real / non-demo organizations completely intact.
    """
    # Create a non-demo production organization
    prod_org = Organization(
        name="Real Production Corp",
        slug="real-prod-corp",
        currency="USD",
        timezone="America/New_York",
        is_demo=False,
    )
    db_session.add(prod_org)
    await db_session.commit()

    # Seed demo data (creates Nexora Labs Inc with is_demo=True)
    await seed_demo_data(db_session, reset_first=True)

    # Both orgs exist
    all_orgs = (await db_session.execute(select(Organization))).scalars().all()
    assert len(all_orgs) == 2

    # Execute safe scoped reset
    reset_res = await reset_demo_data(db_session)
    assert reset_res["status"] == "reset_complete"
    assert reset_res["demo_organizations_purged"] == 1

    # Real org is preserved
    remaining_orgs = (await db_session.execute(select(Organization))).scalars().all()
    assert len(remaining_orgs) == 1
    assert remaining_orgs[0].slug == "real-prod-corp"
    assert remaining_orgs[0].is_demo is False


@pytest.mark.asyncio
async def test_demo_api_endpoints_success(client: AsyncClient, db_session: AsyncSession):
    """Verifies that the /api/v1/demo endpoints function properly under DEMO_MODE=True."""
    # 1. Seed endpoint
    seed_resp = await client.post("/api/v1/demo/seed")
    assert seed_resp.status_code == 200
    data = seed_resp.json()
    assert "Demo environment seeded successfully" in data["message"]

    # 2. Status endpoint
    status_resp = await client.get("/api/v1/demo/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "active"
    assert status_data["health"]["resources"] == 58
    assert status_data["health"]["cost_records"] == 5220
    assert status_data["health"]["financial_reconciliation"] == "PASS"

    # 3. Reset endpoint
    reset_resp = await client.post("/api/v1/demo/reset")
    assert reset_resp.status_code == 200
    reset_data = reset_resp.json()
    assert "reset successfully" in reset_data["message"]


@pytest.mark.asyncio
async def test_demo_api_guardrail_when_disabled(client: AsyncClient, monkeypatch):
    """Verifies that demo endpoints return 403 Forbidden when settings.DEMO_MODE=False."""
    monkeypatch.setattr(settings, "DEMO_MODE", False)

    status_resp = await client.get("/api/v1/demo/status")
    assert status_resp.status_code == 403
    assert "disabled" in status_resp.json()["detail"].lower()

    seed_resp = await client.post("/api/v1/demo/seed")
    assert seed_resp.status_code == 403

    reset_resp = await client.post("/api/v1/demo/reset")
    assert reset_resp.status_code == 403
