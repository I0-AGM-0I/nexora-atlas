"""
NEXORA ATLAS - Repository Layer Tests
Verifies domain data access operations, aggregations, and isolation.
"""

from decimal import Decimal
from datetime import date, datetime, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
    ScenarioChange,
    Forecast,
)
from app.repositories import (
    OrganizationRepository,
    CloudAccountRepository,
    CloudResourceRepository,
    CostRepository,
    AnomalyRepository,
    OptimizationOpportunityRepository,
    RecommendationRepository,
    ScenarioRepository,
    ForecastRepository,
    AuditLogRepository,
)


@pytest.mark.asyncio
async def test_organization_repository(db_session: AsyncSession):
    repo = OrganizationRepository(db_session)
    org = Organization(name="Repo Org", slug="repo-org")
    await repo.create(org)

    fetched = await repo.get_by_slug("repo-org")
    assert fetched is not None
    assert fetched.name == "Repo Org"

    all_orgs = await repo.list_active()
    assert any(o.slug == "repo-org" for o in all_orgs)


@pytest.mark.asyncio
async def test_cloud_account_and_resource_repository(db_session: AsyncSession):
    org_repo = OrganizationRepository(db_session)
    acc_repo = CloudAccountRepository(db_session)
    res_repo = CloudResourceRepository(db_session)

    org = await org_repo.create(Organization(name="Cloud Org", slug="cloud-org"))
    acc = await acc_repo.create(
        CloudAccount(org_id=org.id, account_id="111222333444", name="Production")
    )

    resource = await res_repo.create(
        CloudResource(
            account_id=acc.id,
            service_name="AmazonEC2",
            resource_type="Instance",
            native_id="i-test123",
            name="test-server",
        )
    )

    # Test query by native id
    found_res = await res_repo.get_by_native_id(acc.id, "i-test123")
    assert found_res is not None
    assert found_res.name == "test-server"

    # Test filtering by service name
    listed = await res_repo.list_by_account(acc.id, service_name="AmazonEC2")
    assert len(listed) == 1
    assert listed[0].id == resource.id


@pytest.mark.asyncio
async def test_cost_repository_aggregations(db_session: AsyncSession):
    org_repo = OrganizationRepository(db_session)
    acc_repo = CloudAccountRepository(db_repo := db_session)
    cost_repo = CostRepository(db_session)

    org = await org_repo.create(Organization(name="Cost Org", slug="cost-org"))
    acc = await acc_repo.create(CloudAccount(org_id=org.id, account_id="555555555555", name="Cost Acc"))

    records = [
        CostRecord(
            account_id=acc.id,
            service_name="AmazonEC2",
            usage_date=date(2026, 9, 1),
            unblended_cost=Decimal("1000.0000"),
            amortized_cost=Decimal("1000.0000"),
        ),
        CostRecord(
            account_id=acc.id,
            service_name="AmazonEC2",
            usage_date=date(2026, 9, 2),
            unblended_cost=Decimal("1500.0000"),
            amortized_cost=Decimal("1500.0000"),
        ),
        CostRecord(
            account_id=acc.id,
            service_name="AmazonRDS",
            usage_date=date(2026, 9, 2),
            unblended_cost=Decimal("800.0000"),
            amortized_cost=Decimal("800.0000"),
        ),
    ]
    await cost_repo.bulk_create(records)

    # Sum spend over date range
    total = await cost_repo.sum_spend(acc.id, date(2026, 9, 1), date(2026, 9, 2))
    assert total == Decimal("3300.0000")

    # Sum by service
    by_service = await cost_repo.sum_spend_by_service(acc.id, date(2026, 9, 1), date(2026, 9, 2))
    assert by_service["AmazonEC2"] == Decimal("2500.0000")
    assert by_service["AmazonRDS"] == Decimal("800.0000")


@pytest.mark.asyncio
async def test_anomaly_repository(db_session: AsyncSession):
    org_repo = OrganizationRepository(db_session)
    acc_repo = CloudAccountRepository(db_session)
    anom_repo = AnomalyRepository(db_session)

    org = await org_repo.create(Organization(name="Anom Org", slug="anom-org"))
    acc = await acc_repo.create(CloudAccount(org_id=org.id, account_id="777777777777", name="Anom Acc"))

    await anom_repo.create(
        Anomaly(
            account_id=acc.id,
            service_name="AmazonEC2",
            observed_cost=Decimal("50000.0000"),
            baseline_cost=Decimal("30000.0000"),
            percentage_change=Decimal("66.67"),
            detected_at=datetime.now(timezone.utc),
            detection_rule="RULE_A",
            severity="HIGH",
            status="OPEN",
            confidence_pct=Decimal("90.00"),
        )
    )

    open_count = await anom_repo.get_open_count(acc.id)
    assert open_count == 1

    anomalies = await anom_repo.list_by_account(acc.id, severity="HIGH")
    assert len(anomalies) == 1
    assert anomalies[0].service_name == "AmazonEC2"


@pytest.mark.asyncio
async def test_optimization_and_recommendation_repository(db_session: AsyncSession):
    org_repo = OrganizationRepository(db_session)
    acc_repo = CloudAccountRepository(db_session)
    opp_repo = OptimizationOpportunityRepository(db_session)
    rec_repo = RecommendationRepository(db_session)

    org = await org_repo.create(Organization(name="Opt Repo Org", slug="opt-repo-org"))
    acc = await acc_repo.create(CloudAccount(org_id=org.id, account_id="444333222111", name="Acc"))

    opp = await opp_repo.create(
        OptimizationOpportunity(
            account_id=acc.id,
            category="COMPUTE",
            waste_type="IDLE",
            estimated_waste_monthly=Decimal("12000.0000"),
            evidence_json={"idle_hours": 720},
        )
    )

    rec = await rec_repo.create(
        Recommendation(
            opportunity_id=opp.id,
            category="COMPUTE",
            title="Stop Idle Instance",
            current_configuration="Running 24/7",
            recommended_configuration="Auto-stop off hours",
            estimated_monthly_savings=Decimal("8000.0000"),
            estimated_annual_savings=Decimal("96000.0000"),
            confidence_pct=Decimal("95.00"),
            risk_level="LOW",
            reasoning="Development instance with zero utilization after 18:00",
            status="OPEN",
        )
    )

    total_savings = await rec_repo.sum_potential_savings()
    assert total_savings == Decimal("8000.0000")

    rec_with_evidence = await rec_repo.get_with_evidence(rec.id)
    assert rec_with_evidence is not None
    assert rec_with_evidence.opportunity.waste_type == "IDLE"


@pytest.mark.asyncio
async def test_audit_log_immutability(db_session: AsyncSession):
    org_repo = OrganizationRepository(db_session)
    audit_repo = AuditLogRepository(db_session)

    org = await org_repo.create(Organization(name="Audit Org", slug="audit-org"))
    entry = await audit_repo.log_event(
        org_id=org.id,
        actor_id="admin-user",
        action="CONFIG_UPDATED",
        entity_type="Settings",
        metadata_json={"key": "threshold", "new_value": 2.5},
    )

    assert entry.id is not None
    recent = await audit_repo.list_recent(org.id)
    assert len(recent) == 1
    assert recent[0].action == "CONFIG_UPDATED"

    # Verify immutability guardrails
    with pytest.raises(NotImplementedError):
        await audit_repo.delete_by_id(entry.id)

    with pytest.raises(NotImplementedError):
        await audit_repo.update(entry)
