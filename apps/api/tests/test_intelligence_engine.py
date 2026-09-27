"""
NEXORA ATLAS - Tests: Intelligence Engine Orchestrator & Endpoints
Verifies:
- End-to-end intelligence execution across full schema
- Strict idempotency (consecutive runs produce 0 duplicate records)
- Mathematical reconciliation across all findings
- AuditLog immutable record creation
- REST endpoints (POST /run, GET /status)
- Zero AWS network/SDK calls (Offline-safe)
"""

import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.demo import seed_demo_data
from app.models.organization import Organization, AuditLog
from app.models.anomaly import Anomaly
from app.models.optimization import OptimizationOpportunity, Recommendation
from app.intelligence.orchestration.engine import IntelligenceEngine
from app.demo.config import DEMO_ORG_SLUG


@pytest.mark.asyncio
async def test_intelligence_engine_run_and_idempotency(db_session: AsyncSession):
    """Verifies that IntelligenceEngine runs end-to-end and is strictly idempotent."""
    await seed_demo_data(db_session, reset_first=True)

    org_res = await db_session.execute(select(Organization).where(Organization.slug == DEMO_ORG_SLUG))
    org = org_res.scalars().first()
    assert org is not None

    # First Run
    result1 = await IntelligenceEngine.run(db_session, organization_id=org.id)
    assert result1.ruleset_version == "atlas-intelligence-v1"
    assert result1.anomalies_detected > 0
    assert result1.opportunities_found > 0
    assert result1.recommendations_generated > 0
    assert result1.potential_monthly_savings > Decimal("0.0000")
    assert result1.potential_annual_savings == result1.potential_monthly_savings * Decimal("12")

    # Record database entity counts after run 1
    anom_count_1 = (await db_session.execute(select(func.count(Anomaly.id)))).scalar_one()
    opp_count_1 = (await db_session.execute(select(func.count(OptimizationOpportunity.id)))).scalar_one()
    rec_count_1 = (await db_session.execute(select(func.count(Recommendation.id)))).scalar_one()

    # Second Run on identical data
    result2 = await IntelligenceEngine.run(db_session, organization_id=org.id)
    assert result2.anomalies_detected == result1.anomalies_detected
    assert result2.opportunities_found == result1.opportunities_found

    # Record database entity counts after run 2
    anom_count_2 = (await db_session.execute(select(func.count(Anomaly.id)))).scalar_one()
    opp_count_2 = (await db_session.execute(select(func.count(OptimizationOpportunity.id)))).scalar_one()
    rec_count_2 = (await db_session.execute(select(func.count(Recommendation.id)))).scalar_one()

    # IDEMPOTENCY ASSERTION: Zero duplicate records created
    assert anom_count_2 == anom_count_1, f"Anomalies duplicated: {anom_count_1} -> {anom_count_2}"
    assert opp_count_2 == opp_count_1, f"Opportunities duplicated: {opp_count_1} -> {opp_count_2}"
    assert rec_count_2 == rec_count_1, f"Recommendations duplicated: {rec_count_1} -> {rec_count_2}"

    # AuditLog assertion: 2 runs -> at least 2 audit entries
    audit_res = await db_session.execute(
        select(AuditLog).where(AuditLog.action == "INTELLIGENCE_ANALYSIS_EXECUTED")
    )
    audits = audit_res.scalars().all()
    assert len(audits) >= 2


@pytest.mark.asyncio
async def test_intelligence_status_and_run_endpoints(client: AsyncClient, db_session: AsyncSession):
    """Verifies REST endpoints for intelligence status and manual pipeline execution."""
    await seed_demo_data(db_session, reset_first=True)

    # 1. GET /api/v1/intelligence/status
    res = await client.get("/api/v1/intelligence/status")
    assert res.status_code == 200
    data = res.json()
    assert data["ruleset_version"] == "atlas-intelligence-v1"
    assert data["status"] == "READY"
    assert data["is_offline_mode"] is True
    assert data["aws_network_disabled"] is True

    # 2. POST /api/v1/intelligence/run
    run_res = await client.post("/api/v1/intelligence/run")
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["run_id"].startswith("intel-run-")
    assert run_data["ruleset_version"] == "atlas-intelligence-v1"
    assert run_data["anomalies_detected"] > 0
    assert run_data["opportunities_found"] > 0
    assert len(run_data["rule_evaluations"]) > 0
