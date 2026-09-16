"""
NEXORA ATLAS - Database Model & Schema Tests
Verifies model creation, relationships, decimal precision, timestamps, JSON, and constraints.
"""

from decimal import Decimal
from datetime import date, datetime, timezone
import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Organization,
    CloudAccount,
    CloudRegion,
    CloudResource,
    Tag,
    CostRecord,
    CostSnapshot,
    Anomaly,
    OptimizationOpportunity,
    Recommendation,
    Scenario,
    ScenarioChange,
    Forecast,
    Integration,
    SyncJob,
    AuditLog,
)


@pytest.mark.asyncio
async def test_organization_and_audit_log(db_session: AsyncSession):
    """Verify Organization tenant model and append-only AuditLog."""
    org = Organization(
        name="Nexora Labs Inc",
        slug="nexora-labs",
        currency="INR",
        timezone="Asia/Kolkata",
        is_demo=True,
    )
    db_session.add(org)
    await db_session.flush()

    assert org.id is not None
    assert len(org.id) == 36
    assert org.slug == "nexora-labs"
    assert org.created_at is not None

    # Add audit log
    audit = AuditLog(
        org_id=org.id,
        actor_id="system-bootstrap",
        action="ORGANIZATION_INITIALIZED",
        entity_type="Organization",
        entity_id=org.id,
        metadata_json={"seed_source": "manual_test"},
    )
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    assert audit.id is not None
    assert audit.org_id == org.id
    assert audit.metadata_json["seed_source"] == "manual_test"


@pytest.mark.asyncio
async def test_account_resource_cost_hierarchy(db_session: AsyncSession):
    """Verify tenant hierarchy: Organization -> CloudAccount -> CloudResource -> CostRecord."""
    org = Organization(name="FinOps Corp", slug="finops-corp")
    db_session.add(org)
    await db_session.flush()

    region = CloudRegion(region_code="us-east-1", display_name="US East (N. Virginia)")
    account = CloudAccount(
        org_id=org.id,
        provider_type="AWS",
        account_id="123456789012",
        name="Production Core",
    )
    db_session.add_all([region, account])
    await db_session.flush()

    resource = CloudResource(
        account_id=account.id,
        region_id=region.id,
        service_name="AmazonEC2",
        resource_type="Instance",
        resource_arn="arn:aws:ec2:us-east-1:123456789012:instance/i-0abcdef1234567890",
        native_id="i-0abcdef1234567890",
        name="prod-api-worker-01",
        status="ACTIVE",
        specs_json={"instance_type": "m5.4xlarge", "vcpus": 16, "memory_gb": 64},
    )
    db_session.add(resource)
    await db_session.flush()

    # Add Tag
    tag = Tag(resource_id=resource.id, key="Environment", value="Production")
    db_session.add(tag)

    # Add CostRecord with precise decimal
    exact_cost = Decimal("14285.7143")
    cost_record = CostRecord(
        account_id=account.id,
        resource_id=resource.id,
        service_name="AmazonEC2",
        usage_date=date(2026, 9, 1),
        unblended_cost=exact_cost,
        amortized_cost=exact_cost,
        usage_quantity=Decimal("720.0000"),
        usage_unit="Hrs",
        currency="INR",
    )
    db_session.add(cost_record)
    await db_session.commit()

    # Query back and verify decimal fidelity
    result = await db_session.execute(select(CostRecord).where(CostRecord.id == cost_record.id))
    fetched_record = result.scalars().first()
    assert fetched_record is not None
    assert fetched_record.unblended_cost == exact_cost
    assert isinstance(fetched_record.unblended_cost, Decimal)


@pytest.mark.asyncio
async def test_tag_uniqueness_constraint(db_session: AsyncSession):
    """Verify that a resource cannot hold duplicate tags with the identical key."""
    org = Organization(name="Tag Test Org", slug="tag-test-org")
    db_session.add(org)
    await db_session.flush()

    account = CloudAccount(org_id=org.id, account_id="999999999999", name="Tag Acc")
    db_session.add(account)
    await db_session.flush()

    resource = CloudResource(
        account_id=account.id,
        service_name="AmazonS3",
        resource_type="Bucket",
        native_id="prod-assets-bucket",
    )
    db_session.add(resource)
    await db_session.flush()

    tag1 = Tag(resource_id=resource.id, key="Owner", value="PlatformTeam")
    db_session.add(tag1)
    await db_session.commit()

    # Attempt inserting duplicate key on same resource
    tag2 = Tag(resource_id=resource.id, key="Owner", value="SecurityTeam")
    db_session.add(tag2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_anomaly_observed_vs_inference(db_session: AsyncSession):
    """Verify Anomaly preserves distinct observed facts vs inferences."""
    org = Organization(name="Anomaly Org", slug="anomaly-org")
    db_session.add(org)
    await db_session.flush()

    account = CloudAccount(org_id=org.id, account_id="111222333444", name="Prod")
    db_session.add(account)
    await db_session.flush()

    anomaly = Anomaly(
        account_id=account.id,
        service_name="AmazonEC2",
        observed_cost=Decimal("470000.0000"),
        baseline_cost=Decimal("320000.0000"),
        percentage_change=Decimal("46.88"),
        detected_at=datetime.now(timezone.utc),
        detection_rule="ROLLING_ZSCORE_EXCEEDED",
        observed_metrics_json={"observed_hours": 720, "baseline_hours": 490},
        severity="HIGH",
        status="OPEN",
        inferred_cause="New high-compute batch workload detected in us-east-1",
        confidence_pct=Decimal("91.50"),
        inference_details_json={"correlated_service": "AmazonEKS"},
    )
    db_session.add(anomaly)
    await db_session.commit()
    await db_session.refresh(anomaly)

    assert anomaly.observed_cost == Decimal("470000.0000")
    assert anomaly.confidence_pct == Decimal("91.50")
    assert anomaly.inferred_cause is not None
    assert anomaly.observed_metrics_json["observed_hours"] == 720


@pytest.mark.asyncio
async def test_opportunity_and_recommendation_relationship(db_session: AsyncSession):
    """Verify OptimizationOpportunity -> Recommendation 1-to-many relationship."""
    org = Organization(name="Opt Org", slug="opt-org")
    db_session.add(org)
    await db_session.flush()

    account = CloudAccount(org_id=org.id, account_id="555666777888", name="Opt Acc")
    db_session.add(account)
    await db_session.flush()

    resource = CloudResource(
        account_id=account.id,
        service_name="AmazonEC2",
        resource_type="Instance",
        native_id="i-oversized001",
    )
    db_session.add(resource)
    await db_session.flush()

    opp = OptimizationOpportunity(
        account_id=account.id,
        resource_id=resource.id,
        category="COMPUTE",
        waste_type="OVERSIZED_INSTANCE",
        severity="MEDIUM",
        status="OPEN",
        estimated_waste_monthly=Decimal("34200.0000"),
        evidence_json={"observed_days": 30, "p95_cpu": 11.2, "p95_ram": 18.0},
    )
    db_session.add(opp)
    await db_session.flush()

    # Create two candidate recommendations for this single opportunity
    rec1 = Recommendation(
        opportunity_id=opp.id,
        resource_id=resource.id,
        category="COMPUTE",
        title="Right-size to m5.large",
        current_configuration="m5.4xlarge (16 vCPU, 64 GB)",
        recommended_configuration="m5.large (2 vCPU, 8 GB)",
        estimated_monthly_savings=Decimal("34200.0000"),
        estimated_annual_savings=Decimal("410400.0000"),
        confidence_pct=Decimal("94.00"),
        risk_level="LOW",
        reasoning="Resource is consistently underutilized relative to provisioned headroom.",
        status="OPEN",
    )
    rec2 = Recommendation(
        opportunity_id=opp.id,
        resource_id=resource.id,
        category="COMPUTE",
        title="Migrate to Graviton c7g.large",
        current_configuration="m5.4xlarge (16 vCPU, 64 GB)",
        recommended_configuration="c7g.large (2 vCPU, 4 GB)",
        estimated_monthly_savings=Decimal("38500.0000"),
        estimated_annual_savings=Decimal("462000.0000"),
        confidence_pct=Decimal("82.00"),
        risk_level="MEDIUM",
        reasoning="Graviton architecture yields superior price-performance.",
        status="OPEN",
    )
    db_session.add_all([rec1, rec2])
    await db_session.commit()

    # Query opportunity with recommendations
    result = await db_session.execute(
        select(OptimizationOpportunity)
        .options(selectinload(OptimizationOpportunity.recommendations))
        .where(OptimizationOpportunity.id == opp.id)
    )
    fetched_opp = result.scalars().first()
    assert fetched_opp is not None
    assert len(fetched_opp.recommendations) == 2


@pytest.mark.asyncio
async def test_scenario_and_changes(db_session: AsyncSession):
    """Verify Scenario simulation with child ScenarioChanges."""
    org = Organization(name="Scenario Org", slug="scenario-org")
    db_session.add(org)
    await db_session.flush()

    scenario = Scenario(
        org_id=org.id,
        name="Aggressive EC2 Right-Sizing",
        description="Downsize all development and staging compute",
        baseline_monthly_cost=Decimal("2140000.0000"),
        projected_monthly_cost=Decimal("1890000.0000"),
        monthly_savings=Decimal("250000.0000"),
        percentage_savings=Decimal("11.68"),
        performance_risk="LOW",
        reliability_risk="LOW",
        complexity_level="LOW",
        assumptions_json={"coverage": "Dev/Staging accounts only"},
    )
    db_session.add(scenario)
    await db_session.flush()

    change = ScenarioChange(
        scenario_id=scenario.id,
        change_type="RIGHTSIZE",
        current_spec="m5.4xlarge",
        proposed_spec="m5.large",
        delta_cost=Decimal("-34200.0000"),
    )
    db_session.add(change)
    await db_session.commit()

    result = await db_session.execute(
        select(Scenario)
        .options(selectinload(Scenario.changes))
        .where(Scenario.id == scenario.id)
    )
    fetched_scenario = result.scalars().first()
    assert fetched_scenario is not None
    assert len(fetched_scenario.changes) == 1
    assert fetched_scenario.changes[0].delta_cost == Decimal("-34200.0000")


@pytest.mark.asyncio
async def test_forecast_model(db_session: AsyncSession):
    """Verify Forecast statistical bounds model."""
    org = Organization(name="Forecast Org", slug="forecast-org")
    db_session.add(org)
    await db_session.flush()

    account = CloudAccount(org_id=org.id, account_id="888999000111", name="Forecast Acc")
    db_session.add(account)
    await db_session.flush()

    forecast = Forecast(
        account_id=account.id,
        forecast_month=date(2026, 12, 1),
        projected_cost=Decimal("3140000.0000"),
        lower_bound=Decimal("2950000.0000"),
        upper_bound=Decimal("3330000.0000"),
        confidence_pct=Decimal("88.50"),
        cost_drivers_json=[
            {"service": "AmazonEC2", "driver_weight": 0.45},
            {"service": "AmazonRDS", "driver_weight": 0.25},
        ],
        algorithm="EXPONENTIAL_SMOOTHING",
    )
    db_session.add(forecast)
    await db_session.commit()

    result = await db_session.execute(select(Forecast).where(Forecast.id == forecast.id))
    fetched = result.scalars().first()
    assert fetched is not None
    assert fetched.projected_cost == Decimal("3140000.0000")
    assert len(fetched.cost_drivers_json) == 2
