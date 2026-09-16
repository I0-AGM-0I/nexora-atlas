"""
NEXORA ATLAS - Deterministic Demo Dataset Seeder
Orchestrates high-performance batched database population.
"""

from decimal import Decimal
from typing import Dict, Any
from sqlalchemy import select
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
from app.demo.config import (
    DEMO_ORG_NAME,
    DEMO_ORG_SLUG,
    DEMO_CURRENCY,
    DEMO_TIMEZONE,
    DEMO_ACCOUNTS,
    DEMO_REGIONS,
)
from app.demo.fixtures import get_resource_fixtures
from app.demo.generators.costs import generate_cost_history
from app.demo.generators.anomalies import generate_anomalies
from app.demo.generators.opportunities import generate_opportunities_and_recommendations
from app.demo.generators.scenarios import generate_scenarios
from app.demo.generators.forecasts import generate_forecasts
from app.demo.reset import reset_demo_data
from app.core.logging import logger


async def seed_demo_data(session: AsyncSession, reset_first: bool = True) -> Dict[str, Any]:
    """
    Seeds the complete deterministic synthetic cloud environment for NEXORA ATLAS.
    Completely offline - zero AWS SDK or network calls.
    """
    if reset_first:
        await reset_demo_data(session)

    # Check for existing demo organization (idempotency guardrail)
    existing_org = await session.execute(
        select(Organization).where(Organization.slug == DEMO_ORG_SLUG)
    )
    if existing_org.scalars().first():
        logger.info("Demo organization already exists. Idempotent return.")
        return {"status": "already_seeded", "organization": DEMO_ORG_NAME}

    logger.info(f"Seeding deterministic demo environment for {DEMO_ORG_NAME}...")

    # 1. Create Organization
    org = Organization(
        name=DEMO_ORG_NAME,
        slug=DEMO_ORG_SLUG,
        currency=DEMO_CURRENCY,
        timezone=DEMO_TIMEZONE,
        is_demo=True,
    )
    session.add(org)
    await session.flush()

    # 2. Create Cloud Regions
    region_map: Dict[str, str] = {}  # region_code -> region DB id
    for reg_data in DEMO_REGIONS:
        existing_reg = await session.execute(
            select(CloudRegion).where(
                CloudRegion.region_code == reg_data["region_code"],
                CloudRegion.provider_type == reg_data["provider_type"],
            )
        )
        reg = existing_reg.scalars().first()
        if not reg:
            reg = CloudRegion(
                region_code=reg_data["region_code"],
                display_name=reg_data["display_name"],
                provider_type=reg_data["provider_type"],
            )
            session.add(reg)
            await session.flush()
        region_map[reg.region_code] = reg.id

    # 3. Create Cloud Accounts
    account_map: Dict[str, str] = {}  # raw account_id -> DB id
    for acc_data in DEMO_ACCOUNTS:
        acc = CloudAccount(
            org_id=org.id,
            provider_type=acc_data["provider_type"],
            account_id=acc_data["account_id"],
            name=acc_data["name"],
            status="ACTIVE",
        )
        session.add(acc)
        await session.flush()
        account_map[acc.account_id] = acc.id

    # 4. Create Integration & SyncJob metadata (Offline Demo markers)
    integration = Integration(
        org_id=org.id,
        provider_type="AWS",
        status="CONNECTED",
        auth_method="DEMO_MODE",
        config_json={"environment": "deterministic_synthetic", "provider": "AWS_SIMULATED"},
    )
    session.add(integration)
    await session.flush()

    sync_job = SyncJob(
        integration_id=integration.id,
        account_id=account_map["111222333444"],
        job_type="COST_AND_USAGE_SYNC",
        status="COMPLETED",
        records_synced=6480,
    )
    session.add(sync_job)

    # 5. Create Cloud Resources & Tags
    resource_fixtures = get_resource_fixtures()
    resource_map: Dict[str, str] = {}  # native_id -> DB id
    tags_to_create: List[Tag] = []

    for item in resource_fixtures:
        res = CloudResource(
            account_id=account_map[item["account_id"]],
            region_id=region_map.get(item["region_code"]),
            service_name=item["service_name"],
            resource_type=item["resource_type"],
            resource_arn=item["resource_arn"],
            native_id=item["native_id"],
            name=item["name"],
            status=item["status"],
            specs_json=item["specs_json"],
        )
        session.add(res)
        await session.flush()
        resource_map[res.native_id] = res.id

        # Queue tags
        for k, v in item["tags"].items():
            tags_to_create.append(Tag(resource_id=res.id, key=k, value=v))

    session.add_all(tags_to_create)
    await session.flush()

    # 6. Generate 90-Day Cost Records & Snapshots
    cost_records_data, snapshots_data = generate_cost_history(
        resource_fixtures, account_map, resource_map
    )

    # Batch insert cost records (chunks of 1,000 for high performance)
    cost_record_models = [CostRecord(**rec) for rec in cost_records_data]
    chunk_size = 1000
    for i in range(0, len(cost_record_models), chunk_size):
        session.add_all(cost_record_models[i : i + chunk_size])
        await session.flush()

    # Insert cost snapshots
    snapshot_models = [CostSnapshot(**snap) for snap in snapshots_data]
    session.add_all(snapshot_models)
    await session.flush()

    # 7. Generate Anomalies
    anomalies_data = generate_anomalies(account_map, resource_map)
    anomaly_models = [Anomaly(**anom) for anom in anomalies_data]
    session.add_all(anomaly_models)
    await session.flush()

    # 8. Generate Optimization Opportunities & Recommendations
    opps_data, recs_data = generate_opportunities_and_recommendations(account_map, resource_map)
    opp_ref_map: Dict[str, str] = {}

    for o in opps_data:
        ref = o.pop("_ref")
        opp_model = OptimizationOpportunity(**o)
        session.add(opp_model)
        await session.flush()
        opp_ref_map[ref] = opp_model.id

    for r in recs_data:
        opp_ref = r.pop("opportunity_ref")
        r["opportunity_id"] = opp_ref_map[opp_ref]
        session.add(Recommendation(**r))
    await session.flush()

    # 9. Generate Scenarios & Scenario Changes
    scenarios_data = generate_scenarios(org.id, resource_map)
    for sc in scenarios_data:
        changes = sc.pop("changes")
        sc_model = Scenario(**sc)
        session.add(sc_model)
        await session.flush()

        for ch in changes:
            ch["scenario_id"] = sc_model.id
            session.add(ScenarioChange(**ch))
    await session.flush()

    # 10. Generate Forecasts
    forecasts_data = generate_forecasts(account_map)
    session.add_all([Forecast(**f) for f in forecasts_data])

    # 11. Record Initial Audit Log
    audit = AuditLog(
        org_id=org.id,
        actor_id="system-seeder",
        action="DEMO_DATASET_INITIALIZED",
        entity_type="Organization",
        entity_id=org.id,
        metadata_json={
            "resources_seeded": len(resource_fixtures),
            "cost_records_seeded": len(cost_records_data),
            "opportunities_seeded": len(opps_data),
            "recommendations_seeded": len(recs_data),
            "anomalies_seeded": len(anomalies_data),
            "scenarios_seeded": len(scenarios_data),
        },
    )
    session.add(audit)

    await session.commit()
    logger.info("Deterministic demo environment seeded successfully!")

    return {
        "status": "seeded",
        "organization": DEMO_ORG_NAME,
        "accounts": len(DEMO_ACCOUNTS),
        "regions": len(DEMO_REGIONS),
        "resources": len(resource_fixtures),
        "tags": len(tags_to_create),
        "cost_records": len(cost_records_data),
        "cost_snapshots": len(snapshots_data),
        "anomalies": len(anomalies_data),
        "optimization_opportunities": len(opps_data),
        "recommendations": len(recs_data),
        "scenarios": len(scenarios_data),
        "forecasts": len(forecasts_data),
    }
