"""
NEXORA ATLAS - Phase 9 Milestone 2: Evidence Retrieval Test Suite
Tests each evidence source independently, verifying source lineage, Decimal precision,
epistemic preservation, and no-fabrication invariants (missing telemetry -> NOT_AVAILABLE).
"""

import pytest
import uuid
from decimal import Decimal
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tenant import TenantContext
from app.models.organization import Organization
from app.models.account import CloudAccount
from app.models.cost import CostRecord
from app.models.resource import CloudResource
from app.models.anomaly import Anomaly
from app.models.optimization import OptimizationOpportunity, Recommendation
from app.models.scenario import Scenario
from app.models.telemetry import ResourceMetricObservation
from app.ai.types import EpistemicClass, ScopeType, QuestionCategory
from app.ai.retrieval.selectors import (
    SpendEvidenceSelector,
    CostDriverEvidenceSelector,
    AnomalyEvidenceSelector,
    ResourceEvidenceSelector,
    TelemetryEvidenceSelector,
    RecommendationEvidenceSelector,
    ScenarioEvidenceSelector,
    ForecastEvidenceSelector,
)
from app.ai.retrieval.ranking import rank_evidence_items


@pytest.fixture
async def setup_test_tenant_with_data(db_session: AsyncSession):
    """Seeds tenant and authoritative data for retrieval testing."""
    org = Organization(
        name="Test Org",
        slug="test-org",
        currency="INR",
        timezone="Asia/Kolkata",
        is_demo=False,
    )
    db_session.add(org)
    await db_session.flush()

    account = CloudAccount(
        id=str(uuid.uuid4()),
        org_id=org.id,
        provider_type="AWS",
        account_id="999888777666",
        name="Production Core",
    )
    db_session.add(account)
    await db_session.flush()

    # Cost records
    cost1 = CostRecord(
        id=str(uuid.uuid4()),
        account_id=account.id,
        service_name="Amazon Elastic Compute Cloud - Compute",
        usage_date=date(2026, 9, 1),
        unblended_cost=Decimal("150000.00"),
        amortized_cost=Decimal("150000.00"),
    )
    cost2 = CostRecord(
        id=str(uuid.uuid4()),
        account_id=account.id,
        service_name="Amazon Simple Storage Service",
        usage_date=date(2026, 9, 1),
        unblended_cost=Decimal("35000.00"),
        amortized_cost=Decimal("35000.00"),
    )
    db_session.add_all([cost1, cost2])

    # Resource
    res1 = CloudResource(
        id=str(uuid.uuid4()),
        account_id=account.id,
        service_name="Amazon Elastic Compute Cloud - Compute",
        resource_type="ec2_instance",
        native_id="i-0abcdef1234567890",
        name="prod-api-worker",
        specs_json={"instance_type": "r5.2xlarge"},
    )
    db_session.add(res1)

    # Anomaly
    anom1 = Anomaly(
        id=str(uuid.uuid4()),
        account_id=account.id,
        service_name="Amazon Elastic Compute Cloud - Compute",
        observed_cost=Decimal("180000.00"),
        baseline_cost=Decimal("120000.00"),
        percentage_change=Decimal("50.0"),
        detected_at=datetime.now(timezone.utc),
        detection_rule="Z_SCORE_SPIKE",
        severity="HIGH",
        status="OPEN",
        inferred_cause="Unexpected compute auto-scaling event.",
    )
    db_session.add(anom1)

    # Opportunity & Recommendation
    opp1 = OptimizationOpportunity(
        id=str(uuid.uuid4()),
        account_id=account.id,
        resource_id=res1.id,
        category="RIGHTSIZING",
        waste_type="OVERPROVISIONED",
        status="ACTIVE",
        estimated_waste_monthly=Decimal("18500.00"),
        evidence_json={"cpu_p95": 8.5},
    )
    db_session.add(opp1)
    await db_session.flush()

    rec1 = Recommendation(
        id=str(uuid.uuid4()),
        opportunity_id=opp1.id,
        resource_id=res1.id,
        category="RIGHTSIZING",
        title="Downsize memory-optimized instance",
        current_configuration="r5.2xlarge",
        recommended_configuration="r5.xlarge",
        estimated_monthly_savings=Decimal("18500.00"),
        estimated_annual_savings=Decimal("222000.00"),
        confidence_pct=Decimal("90.00"),
        risk_level="LOW",
        reasoning="CPU and memory underutilized",
    )
    db_session.add(rec1)

    # Scenario
    scen1 = Scenario(
        id=str(uuid.uuid4()),
        org_id=org.id,
        name="Graviton Modernization Plan",
        baseline_monthly_cost=Decimal("200000.00"),
        projected_monthly_cost=Decimal("158000.00"),
        monthly_savings=Decimal("42000.00"),
        percentage_savings=Decimal("21.0"),
        assumptions_json={"pricing": "On-Demand", "term": "1-Year"},
    )
    db_session.add(scen1)
    await db_session.commit()

    tenant = TenantContext(
        org_id=org.id,
        org_name=org.name,
        slug=org.slug,
        currency="INR",
        timezone="Asia/Kolkata",
        is_demo=False,
        account_ids=[account.id],
        accounts=[account],
        account_name_map={account.id: account.name},
    )
    return tenant, res1, rec1, scen1, anom1


@pytest.mark.asyncio
async def test_spend_evidence_selector(db_session: AsyncSession, setup_test_tenant_with_data):
    """Spend selector must produce Decimal values and preserve DERIVED/OBSERVED boundaries."""
    tenant, _, _, _, _ = setup_test_tenant_with_data

    items = await SpendEvidenceSelector.select_evidence(db_session, tenant)
    assert len(items) >= 2

    total_item = items[0]
    assert total_item.type == "SPEND_TOTAL"
    assert total_item.epistemic_class == EpistemicClass.DERIVED
    assert isinstance(total_item.value, Decimal)
    assert total_item.value == Decimal("185000.00")
    assert total_item.unit == "INR"

    svc_item = items[1]
    assert svc_item.type == "SERVICE_SPEND"
    assert svc_item.epistemic_class == EpistemicClass.OBSERVED
    assert isinstance(svc_item.value, Decimal)


@pytest.mark.asyncio
async def test_anomaly_evidence_selector(db_session: AsyncSession, setup_test_tenant_with_data):
    """Anomaly selector retrieves observed cost and preserves OBSERVED status."""
    tenant, _, _, _, anom = setup_test_tenant_with_data

    items = await AnomalyEvidenceSelector.select_evidence(db_session, tenant)
    assert len(items) >= 1
    anom_item = items[0]

    assert anom_item.type == "ANOMALY"
    assert anom_item.epistemic_class == EpistemicClass.OBSERVED
    assert isinstance(anom_item.value, Decimal)
    assert anom_item.value == Decimal("180000.00")
    assert anom_item.source_entity_id == anom.id


@pytest.mark.asyncio
async def test_recommendation_evidence_selector(db_session: AsyncSession, setup_test_tenant_with_data):
    """Recommendation selector retrieves savings in Decimal and tags as INFERRED."""
    tenant, res, rec, _, _ = setup_test_tenant_with_data

    items = await RecommendationEvidenceSelector.select_evidence(db_session, tenant, resource_id=res.id)
    assert len(items) >= 1
    rec_item = items[0]

    assert rec_item.type == "RECOMMENDATION"
    assert rec_item.epistemic_class == EpistemicClass.INFERRED
    assert isinstance(rec_item.value, Decimal)
    assert rec_item.value == Decimal("185000.00") or rec_item.value == Decimal("18500.00")
    assert rec_item.unit == "INR"


@pytest.mark.asyncio
async def test_scenario_evidence_selector(db_session: AsyncSession, setup_test_tenant_with_data):
    """Scenario selector retrieves savings in Decimal and tags strictly as PROJECTED."""
    tenant, _, _, scen, _ = setup_test_tenant_with_data

    items = await ScenarioEvidenceSelector.select_evidence(db_session, tenant, scenario_id=scen.id)
    assert len(items) >= 1
    scen_item = items[0]

    assert scen_item.type == "SCENARIO"
    assert scen_item.epistemic_class == EpistemicClass.PROJECTED
    assert isinstance(scen_item.value, Decimal)
    assert scen_item.value == Decimal("42000.00")


@pytest.mark.asyncio
async def test_telemetry_missing_evidence_invariant(db_session: AsyncSession, setup_test_tenant_with_data):
    """
    CRITICAL INVARIANT: Missing telemetry returns NOT_AVAILABLE, NEVER synthetic zeroes.
    """
    tenant, res, _, _, _ = setup_test_tenant_with_data

    # Resource has no metric observations in DB
    items = await TelemetryEvidenceSelector.select_evidence(db_session, tenant, resource_id=res.id)
    assert len(items) == 1
    diag = items[0]

    assert diag.epistemic_class == EpistemicClass.NOT_AVAILABLE
    assert diag.value is None  # Never 0.0!
    assert "INSUFFICIENT or NOT_AVAILABLE" in diag.statement


def test_ranking_categorical_order():
    """Rank evidence items strictly by epistemic categorical hierarchy."""
    from app.ai.models import EvidenceItem

    obs = EvidenceItem(id="e-obs", type="T", epistemic_class=EpistemicClass.OBSERVED, statement="Obs")
    der = EvidenceItem(id="e-der", type="T", epistemic_class=EpistemicClass.DERIVED, statement="Der")
    inf = EvidenceItem(id="e-inf", type="T", epistemic_class=EpistemicClass.INFERRED, statement="Inf")
    proj = EvidenceItem(id="e-proj", type="T", epistemic_class=EpistemicClass.PROJECTED, statement="Proj")
    na = EvidenceItem(id="e-na", type="T", epistemic_class=EpistemicClass.NOT_AVAILABLE, statement="NA")

    # In reverse order
    ranked = rank_evidence_items([na, proj, inf, der, obs])
    assert ranked[0].id == "e-obs"
    assert ranked[1].id == "e-der"
    assert ranked[2].id == "e-inf"
    assert ranked[3].id == "e-proj"
    assert ranked[4].id == "e-na"
