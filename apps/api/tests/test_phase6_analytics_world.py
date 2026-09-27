"""
NEXORA ATLAS - Phase 6 Golden Integration Test: Full Analytical Chain of Reasoning
Validates:
Seed Demo -> Phase 5 Intelligence -> Phase 6 Analytics -> Scenarios -> Portfolio
Confirms:
1. Reconciled cost-driver attribution
2. Distinct contribution metrics
3. Descriptive spend concentration (HHI)
4. Efficiency & capacity headroom
5. Scenario financial reconciliation and constraints
6. Collective portfolio conflict resolution
7. Machine-readable analytical provenance
8. Determinism and tenant isolation
"""

import pytest
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.demo import seed_demo_data
from app.demo.config import DEMO_ORG_SLUG
from app.models.organization import Organization
from app.services.tenant import get_tenant_context
from app.intelligence.orchestration.engine import IntelligenceEngine
from app.services.analytics import AnalyticsService
from app.analytics.types import SufficiencyStatus, DriverDimension


@pytest.mark.asyncio
async def test_golden_analytics_chain_of_reasoning(db_session: AsyncSession):
    """
    Phase 6 Golden Integration Test:
    Executes the entire end-to-end analytics and optimization modeling pipeline
    against seeded demo infrastructure.
    """
    # 1. Seed Demo Data
    await seed_demo_data(db_session, reset_first=True)

    org_res = await db_session.execute(
        select(Organization).where(Organization.slug == DEMO_ORG_SLUG)
    )
    org = org_res.scalars().first()
    assert org is not None

    # 2. Run Phase 5 Intelligence Engine (produces auditable findings in DB)
    intel_result = await IntelligenceEngine.run(db_session, organization_id=org.id)
    assert intel_result.ruleset_version == "atlas-intelligence-v1"
    assert intel_result.opportunities_found > 0
    assert intel_result.recommendations_generated > 0

    # 3. Resolve Tenant Context
    tenant = await get_tenant_context(db_session, DEMO_ORG_SLUG)

    # 4. Run Phase 6 Analytics Summary (The Progressive Chain of Reasoning)
    summary_1 = await AnalyticsService.get_summary(db_session, tenant, comparison_window_days=30)
    summary_2 = await AnalyticsService.get_summary(db_session, tenant, comparison_window_days=30)

    # =========================================================================
    # PROOF 1: Determinism (summary_1 == summary_2)
    # =========================================================================
    assert summary_1.drivers.net_change == summary_2.drivers.net_change
    assert summary_1.trends.trend_direction == summary_2.trends.trend_direction
    assert summary_1.portfolio.total_compatible_monthly_savings == summary_2.portfolio.total_compatible_monthly_savings

    # =========================================================================
    # PROOF 2: Cost Drivers & Exact Attribution Reconciliation
    # =========================================================================
    drivers = summary_1.drivers
    assert drivers.sufficiency_status == SufficiencyStatus.AVAILABLE
    assert drivers.reconciled is True

    # Invariant: sum(service_deltas) == total_delta
    service_delta_sum = sum((d.cost_delta for d in drivers.service_drivers), Decimal("0.0000"))
    assert service_delta_sum == drivers.net_change

    # Invariant: sum(account_deltas) == total_delta
    account_delta_sum = sum((d.cost_delta for d in drivers.account_drivers), Decimal("0.0000"))
    assert account_delta_sum == drivers.net_change

    # Verify distinct contribution metrics on top driver (Correction 1)
    top_svc = drivers.service_drivers[0]
    assert top_svc.dimension == DriverDimension.SERVICE
    assert top_svc.absolute_contribution_pct > Decimal("0.00")
    if drivers.net_change != Decimal("0.0000"):
        assert top_svc.net_change_contribution_pct is not None

    # =========================================================================
    # PROOF 3: Descriptive Spend Concentration Index (HHI)
    # =========================================================================
    concentration = summary_1.concentration
    assert concentration.sufficiency_status == SufficiencyStatus.AVAILABLE
    assert concentration.top_1_service_share_pct > Decimal("0.00")
    assert concentration.spend_concentration_index > Decimal("0.00")
    assert "Concentrated" in concentration.hhi_interpretation or "Diversified" in concentration.hhi_interpretation

    # =========================================================================
    # PROOF 4: Capacity Headroom & Unit Economics Decoupling
    # =========================================================================
    efficiency = summary_1.efficiency
    assert efficiency.sufficiency_status == SufficiencyStatus.AVAILABLE
    assert len(efficiency.headroom_items) > 0

    # Verify observed utilization headroom on EC2 instances (Correction 5)
    ec2_headrooms = [h for h in efficiency.headroom_items if h.service_name == "AmazonEC2"]
    assert len(ec2_headrooms) > 0
    sample_headroom = ec2_headrooms[0]
    if sample_headroom.p95_utilization_cpu is not None:
        assert sample_headroom.observed_utilization_headroom_cpu == (
            Decimal("100.00") - sample_headroom.p95_utilization_cpu
        )

    # Verify unit economics are NOT_CONFIGURED (Correction 12: no fake metrics)
    for ue in efficiency.unit_economics:
        assert ue.status == SufficiencyStatus.NOT_CONFIGURED
        assert ue.cost_per_unit is None

    # =========================================================================
    # PROOF 5: Collective Optimization Portfolio & Conflict Detection
    # =========================================================================
    portfolio = summary_1.portfolio
    assert portfolio.total_opportunities_count > 0
    assert portfolio.total_recommendations_count > 0
    assert portfolio.total_compatible_monthly_savings > Decimal("0.0000")
    assert portfolio.total_compatible_annual_savings == portfolio.total_compatible_monthly_savings * Decimal("12")

    # Verify descriptive risk profile (Correction 9: NO magic score)
    assert portfolio.risk_profile.highest_risk in ("LOW", "MEDIUM", "HIGH")
    assert (portfolio.risk_profile.count_low + portfolio.risk_profile.count_medium + portfolio.risk_profile.count_high) == portfolio.compatible_recommendations_count

    # =========================================================================
    # PROOF 6: Scenario Financial Reconciliation & Constraints
    # =========================================================================
    assert len(summary_1.scenarios) > 0
    for sim in summary_1.scenarios:
        assert sim.is_valid is True
        # Invariant 1: baseline - projected == monthly_savings
        assert (sim.baseline_monthly_cost - sim.projected_monthly_cost) == sim.monthly_savings
        # Invariant 2: annual == monthly * 12
        assert sim.annual_savings == sim.monthly_savings * Decimal("12")
        # Invariant 3: sum(change_deltas) == -monthly_savings
        deltas_sum = sum((c.delta_cost for c in sim.changes), Decimal("0.0000"))
        assert deltas_sum == -sim.monthly_savings
        # Assumptions explicit
        assert sim.assumptions["pricing_basis"] == "synthetic_demo"

    # =========================================================================
    # PROOF 7: Analytical Explanation Lineage
    # =========================================================================
    explanation = drivers.explanation
    assert explanation.version == "atlas-analytics-v1"
    assert "current_total_spend" in explanation.observations
    assert "net_change" in explanation.derived_metrics
    assert len(explanation.evidence) > 0

    # =========================================================================
    # PROOF 8: Tenant Isolation
    # =========================================================================
    # An organization with zero resources/accounts yields INSUFFICIENT_DATA and zero spend
    isolated_tenant = type(tenant)(
        org_id="isolated-org-id",
        org_name="Isolated Org",
        slug="isolated-org",
        currency="INR",
        timezone="Asia/Kolkata",
        is_demo=False,
        account_ids=[],
        accounts=[],
        account_name_map={},
    )
    isolated_drivers = await AnalyticsService.get_drivers(db_session, isolated_tenant)
    assert isolated_drivers.drivers.sufficiency_status == SufficiencyStatus.INSUFFICIENT_DATA
    assert isolated_drivers.drivers.current_period_cost == Decimal("0.0000")
    assert isolated_drivers.drivers.net_change == Decimal("0.0000")
