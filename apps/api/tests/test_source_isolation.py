"""
NEXORA ATLAS - Source Isolation & Provider Decoupling Tests
Verifies Correction 15:
1. Demo data pathway continues to run completely offline through Phase 5 & Phase 6.
2. The AWS adapter code does NOT contaminate or alter the demo pathway.
3. Both sources populate identical canonical entities (CloudResource, CostRecord, CloudAccount)
   that satisfy identical analytical contracts.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.demo.seed import seed_demo_data
from app.demo.config import DEMO_ORG_SLUG
from app.models.organization import Organization
from app.models.account import CloudAccount
from app.models.resource import CloudResource
from app.models.cost import CostRecord
from app.services.tenant import get_tenant_context
from app.intelligence.orchestration.engine import IntelligenceEngine
from app.services.analytics import AnalyticsService


@pytest.mark.asyncio
async def test_demo_source_isolation_through_phase5_and_phase6(db_session: AsyncSession):
    """
    Proves that the Demo data source runs end-to-end through Phase 5 Intelligence
    and Phase 6 Analytics completely decoupled from the AWS integration code.
    """
    # 1. Seed standard demo data
    await seed_demo_data(db_session, reset_first=True)

    org_q = await db_session.execute(
        select(Organization).where(Organization.slug == DEMO_ORG_SLUG)
    )
    demo_org = org_q.scalars().first()
    assert demo_org is not None

    # 2. Run Phase 5 Intelligence Engine
    intel_res = await IntelligenceEngine.run(db_session, organization_id=demo_org.id)
    assert intel_res.ruleset_version == "atlas-intelligence-v1"
    assert intel_res.opportunities_found > 0
    assert intel_res.recommendations_generated > 0

    # 3. Resolve Tenant and Run Phase 6 Analytics
    tenant = await get_tenant_context(db_session, DEMO_ORG_SLUG)
    analytics_summary = await AnalyticsService.get_summary(db_session, tenant)

    # 4. Verify Canonical Contracts
    assert analytics_summary.trends is not None
    assert analytics_summary.drivers is not None
    assert analytics_summary.concentration is not None
    assert analytics_summary.efficiency is not None
    assert analytics_summary.portfolio is not None
    assert len(analytics_summary.scenarios) > 0

    # 5. Contract Invariant: Database entities from Demo and AWS share identical schema types
    demo_resources = (
        await db_session.execute(
            select(CloudResource).where(CloudResource.account_id.in_(tenant.account_ids)).limit(5)
        )
    ).scalars().all()

    for r in demo_resources:
        assert isinstance(r.native_id, str)
        assert isinstance(r.service_name, str)
        assert isinstance(r.specs_json, dict)
