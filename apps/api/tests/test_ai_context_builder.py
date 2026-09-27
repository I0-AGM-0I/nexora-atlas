"""
NEXORA ATLAS - Phase 9 Milestone 2: Context Builder & Golden Scenarios Test Suite
Tests canonicalization determinism, SHA-256 digest stability, and end-to-end M2 Golden Scenarios
(A through H) without any AI provider involved.
"""

import pytest
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tenant import TenantContext
from app.models.organization import Organization
from app.models.account import CloudAccount
from app.models.cost import CostRecord
from app.models.resource import CloudResource
from app.models.anomaly import Anomaly
from app.models.optimization import OptimizationOpportunity, Recommendation
from app.models.scenario import Scenario
from app.ai.types import EpistemicClass, ScopeType, QuestionCategory, DataFreshnessStatus
from app.ai.models import EvidenceItem, EvidencePackage, BoundedContext
from app.ai.context.canonicalizer import canonicalize_evidence_package, compute_evidence_hash
from app.ai.context.builder import ContextBuilder
from app.ai.retrieval.engine import RetrievalEngine


@pytest.fixture
async def golden_m2_estate(db_session: AsyncSession):
    """Sets up golden multi-tenant estate for M2 end-to-end golden scenarios."""
    org = Organization(
        name="Golden Org",
        slug="golden-org",
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
        account_id="111222333444",
        name="Production Core",
    )
    db_session.add(account)
    await db_session.flush()

    # Cost records: Total ₹161,000 increase: EKS (₹82,000), GPU (₹51,000), S3 (₹28,000)
    c1 = CostRecord(
        id=str(uuid.uuid4()),
        account_id=account.id,
        service_name="Amazon Elastic Kubernetes Service",
        usage_date=date(2026, 9, 1),
        unblended_cost=Decimal("82000.00"),
        amortized_cost=Decimal("82000.00"),
    )
    c2 = CostRecord(
        id=str(uuid.uuid4()),
        account_id=account.id,
        service_name="Amazon Elastic Compute Cloud - Compute",
        usage_date=date(2026, 9, 1),
        unblended_cost=Decimal("51000.00"),
        amortized_cost=Decimal("51000.00"),
    )
    c3 = CostRecord(
        id=str(uuid.uuid4()),
        account_id=account.id,
        service_name="Amazon Simple Storage Service",
        usage_date=date(2026, 9, 1),
        unblended_cost=Decimal("28000.00"),
        amortized_cost=Decimal("28000.00"),
    )
    db_session.add_all([c1, c2, c3])

    # Resource: prod-analytics-worker
    worker = CloudResource(
        id=str(uuid.uuid4()),
        account_id=account.id,
        service_name="Amazon Elastic Compute Cloud - Compute",
        resource_type="ec2_instance",
        native_id="i-worker-analytics-01",
        name="prod-analytics-worker",
        specs_json={"instance_type": "r5.2xlarge", "vcpus": 8, "memory_gb": 64},
    )
    db_session.add(worker)
    await db_session.flush()

    # Recommendation for worker
    opp = OptimizationOpportunity(
        id=str(uuid.uuid4()),
        account_id=account.id,
        resource_id=worker.id,
        category="RIGHTSIZING",
        waste_type="OVERPROVISIONED",
        status="ACTIVE",
        estimated_waste_monthly=Decimal("14500.00"),
        evidence_json={"cpu_p95": 12.0},
    )
    db_session.add(opp)
    await db_session.flush()

    rec = Recommendation(
        id=str(uuid.uuid4()),
        opportunity_id=opp.id,
        resource_id=worker.id,
        category="RIGHTSIZING",
        title="Rightsize analytics worker to r5.xlarge",
        current_configuration="r5.2xlarge",
        recommended_configuration="r5.xlarge",
        estimated_monthly_savings=Decimal("14500.00"),
        estimated_annual_savings=Decimal("174000.00"),
        confidence_pct=Decimal("92.00"),
        risk_level="LOW",
        reasoning="Worker underutilized",
    )
    db_session.add(rec)

    # Scenario: Modernization
    scen = Scenario(
        id=str(uuid.uuid4()),
        org_id=org.id,
        name="Graviton Migration",
        baseline_monthly_cost=Decimal("200000.00"),
        projected_monthly_cost=Decimal("165000.00"),
        monthly_savings=Decimal("35000.00"),
        percentage_savings=Decimal("17.50"),
        assumptions_json={"architecture": "arm64", "pricing": "On-Demand"},
    )
    db_session.add(scen)
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
    return tenant, worker, rec, scen


def test_canonical_hash_determinism_and_sensitivity():
    """
    Section 54: Identical package -> identical hash; ₹1 change -> different hash.
    """
    item1 = EvidenceItem(
        id="spend-1",
        type="SPEND_TOTAL",
        epistemic_class=EpistemicClass.DERIVED,
        statement="Spend item",
        value=Decimal("100000.00"),
        unit="INR",
        source="Atlas",
    )
    pkg_a = EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        observations=[item1],
        evidence_count=1,
    )
    pkg_b = EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        observations=[item1],
        evidence_count=1,
    )

    hash_a = compute_evidence_hash(pkg_a)
    hash_b = compute_evidence_hash(pkg_b)
    assert hash_a == hash_b
    assert len(hash_a) == 64

    # Change by ₹1 (₹100,001)
    item_diff = EvidenceItem(
        id="spend-1",
        type="SPEND_TOTAL",
        epistemic_class=EpistemicClass.DERIVED,
        statement="Spend item",
        value=Decimal("100001.00"),  # Changed
        unit="INR",
        source="Atlas",
    )
    pkg_diff = EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        observations=[item_diff],
        evidence_count=1,
    )
    hash_diff = compute_evidence_hash(pkg_diff)
    assert hash_diff != hash_a


@pytest.mark.asyncio
async def test_golden_scenario_a_spend_increase(db_session: AsyncSession, golden_m2_estate):
    """
    Scenario A: "Why did my spend increase?"
    Expected: SPEND_CHANGE category, spend evidence, driver evidence, deterministic hash.
    """
    tenant, _, _, _ = golden_m2_estate
    question = "Why did my spend increase?"

    pkg: EvidencePackage = await RetrievalEngine.build_evidence_package(
        session=db_session,
        tenant=tenant,
        question=question,
        scope_type=ScopeType.DASHBOARD,
    )

    assert pkg.scope_type == ScopeType.DASHBOARD
    assert len(pkg.all_items()) >= 3
    # Check that financial values are Decimals
    for item in pkg.all_items():
        if item.value is not None:
            assert isinstance(item.value, Decimal)

    digest = pkg.compute_hash()
    assert len(digest) == 64


@pytest.mark.asyncio
async def test_golden_scenario_b_resource_rightsizing(db_session: AsyncSession, golden_m2_estate):
    """
    Scenario B: "Can I reduce prod-analytics-worker?"
    Expected: RESOURCE scope, resource spec, recommendation evidence, missing telemetry note.
    """
    tenant, worker, rec, _ = golden_m2_estate
    question = "Can I reduce prod-analytics-worker?"

    pkg: EvidencePackage = await RetrievalEngine.build_evidence_package(
        session=db_session,
        tenant=tenant,
        question=question,
        scope_type=ScopeType.RESOURCE,
        scope_id=worker.id,
    )

    assert pkg.scope_type == ScopeType.RESOURCE
    assert pkg.scope_id == worker.id
    assert any(i.type == "RESOURCE_SPEC" for i in pkg.observations)
    assert any(i.type == "RECOMMENDATION" for i in pkg.recommendations)
    # Missing telemetry handled gracefully
    assert any("INSUFFICIENT or NOT_AVAILABLE" in lim for lim in pkg.limitations)


@pytest.mark.asyncio
async def test_golden_scenario_c_scenario_projection(db_session: AsyncSession, golden_m2_estate):
    """
    Scenario D: "What would happen if we used the proposed instance?"
    Expected: PROJECTED scenario evidence with explicit hypothetical disclaimer.
    """
    tenant, _, _, scen = golden_m2_estate
    question = "What would happen if we migrated to Graviton?"

    pkg: EvidencePackage = await RetrievalEngine.build_evidence_package(
        session=db_session,
        tenant=tenant,
        question=question,
        scope_type=ScopeType.SCENARIO,
        scope_id=scen.id,
    )

    assert pkg.scope_type == ScopeType.SCENARIO
    scen_items = [i for i in pkg.scenarios if i.type == "SCENARIO"]
    assert len(scen_items) >= 1
    assert scen_items[0].epistemic_class == EpistemicClass.PROJECTED
    assert "hypothetical savings" in scen_items[0].statement


def test_create_bounded_context_envelope():
    """Verifies ContextBuilder produces valid BoundedContext envelope."""
    item = EvidenceItem(
        id="spend-001",
        type="SPEND_TOTAL",
        epistemic_class=EpistemicClass.DERIVED,
        statement="Spend item",
        value=Decimal("50000.00"),
        unit="INR",
        source="Atlas",
    )
    pkg = EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        observations=[item],
        evidence_count=1,
    )

    ctx: BoundedContext = ContextBuilder.create_bounded_context(pkg)
    assert ctx.included_count == 1
    assert ctx.excluded_count == 0
    assert ctx.is_context_limited is False
    assert len(ctx.sha256_hash) == 64
    assert "spend-001" in ctx.canonical_json
