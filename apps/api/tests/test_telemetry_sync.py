"""
NEXORA ATLAS - Telemetry Synchronization Lifecycle Tests
Verifies:
1. End-to-end telemetry ingestion and correlation into canonical ResourceMetricObservation.
2. Exact idempotency (0 duplicates on re-sync).
3. Independent subsystem degradation (CloudWatch failure does not abort Cost/Inventory sync).
"""

from decimal import Decimal
from datetime import datetime, timezone, date, timedelta
from unittest.mock import MagicMock
from sqlalchemy import select
from botocore.exceptions import ClientError
import pytest

from app.models.organization import Organization
from app.models.account import CloudAccount, Integration
from app.models.telemetry import ResourceMetricObservation
from app.integrations.providers.aws.client import AWSClientFactory
from app.integrations.sync.coordinator import SyncCoordinator


@pytest.mark.asyncio
async def test_telemetry_sync_end_to_end_and_idempotency(db_session):
    """Verifies that telemetry is ingested, persisted, and subsequent sync is idempotent."""
    org = Organization(name="Telemetry Org", slug="telemetry-org")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    integration = Integration(
        org_id=org.id,
        provider_type="AWS",
        status="CONFIGURED",
        config_json={
            "role_arn": "arn:aws:iam::123456789012:role/AtlasReadOnlyRole",
            "external_id": "secret-ext-id",
            "region": "us-east-1",
        },
    )
    db_session.add(integration)
    await db_session.commit()
    await db_session.refresh(integration)

    factory = MagicMock(spec=AWSClientFactory)
    factory.role_arn = integration.config_json["role_arn"]
    factory.external_id = integration.config_json["external_id"]
    factory.region_name = "us-east-1"

    # Mock STS
    mock_sts = MagicMock()
    mock_sts.get_caller_identity.return_value = {
        "Account": "123456789012",
        "Arn": factory.role_arn,
    }

    # Mock EC2
    mock_ec2 = MagicMock()
    mock_ec2.describe_regions.return_value = {
        "Regions": [{"RegionName": "us-east-1"}]
    }
    paginator_ec2 = MagicMock()
    paginator_ec2.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-compute-01",
                            "InstanceType": "m5.large",
                            "State": {"Name": "running"},
                            "LaunchTime": datetime(2026, 1, 1, tzinfo=timezone.utc),
                            "Tags": [{"Key": "Name", "Value": "worker-01"}],
                        }
                    ]
                }
            ]
        }
    ]
    # EBS volumes paginator
    paginator_ebs = MagicMock()
    paginator_ebs.paginate.return_value = [{"Volumes": []}]

    def _get_paginator(name):
        if name == "describe_instances":
            return paginator_ec2
        if name == "describe_volumes":
            return paginator_ebs
        return MagicMock()

    mock_ec2.get_paginator.side_effect = _get_paginator

    # Mock RDS, S3, EKS
    mock_rds = MagicMock()
    mock_rds.get_paginator.return_value.paginate.return_value = [{"DBInstances": []}]
    mock_s3 = MagicMock()
    mock_s3.get_paginator.return_value.paginate.return_value = [{"Buckets": []}]
    mock_eks = MagicMock()
    mock_eks.get_paginator.return_value.paginate.return_value = [{"clusters": []}]

    # Mock Cost Explorer
    mock_ce = MagicMock()
    mock_ce.get_cost_and_usage.return_value = {"ResultsByTime": []}
    mock_ce.get_cost_and_usage_with_resources.return_value = {"ResultsByTime": []}

    # Mock CloudWatch (Returns 2 observations for each requested query)
    now = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
    mock_cw = MagicMock()
    mock_cw.get_paginator.return_value.paginate.return_value = [{"Metrics": []}]

    def _mock_get_metric_data(**kwargs):
        queries = kwargs.get("MetricDataQueries", [])
        results = []
        for q in queries:
            results.append(
                {
                    "Id": q["Id"],
                    "Timestamps": [now - timedelta(hours=1), now],
                    "Values": [14.5, 16.2],
                    "StatusCode": "Complete",
                }
            )
        return {"MetricDataResults": results}

    mock_cw.get_metric_data.side_effect = _mock_get_metric_data

    def _get_client(service_name, region=None):
        if service_name == "sts":
            return mock_sts
        if service_name == "ec2":
            return mock_ec2
        if service_name == "rds":
            return mock_rds
        if service_name == "s3":
            return mock_s3
        if service_name == "eks":
            return mock_eks
        if service_name == "ce":
            return mock_ce
        if service_name == "cloudwatch":
            return mock_cw
        return MagicMock()

    factory.get_client.side_effect = _get_client

    # 1. Run Initial Sync
    res1 = await SyncCoordinator.execute_sync(
        session=db_session,
        integration_id=integration.id,
        org_id=org.id,
        client_factory=factory,
        target_end_date=date(2026, 9, 18),
    )

    assert res1["status"] == "COMPLETED"
    assert res1["telemetry_observations_created"] > 0
    assert res1["resources_with_telemetry"] == 1

    # Verify rows in DB (5 EC2 metrics * 2 observations = 10)
    obs_q = await db_session.execute(
        select(ResourceMetricObservation).where(
            ResourceMetricObservation.organization_id == org.id
        )
    )
    obs_rows = obs_q.scalars().all()
    assert len(obs_rows) == 10
    assert res1["telemetry_observations_created"] == 10

    # 2. Run Idempotent Re-Sync with identical data
    res2 = await SyncCoordinator.execute_sync(
        session=db_session,
        integration_id=integration.id,
        org_id=org.id,
        client_factory=factory,
        target_end_date=date(2026, 9, 18),
    )

    assert res2["status"] == "COMPLETED"
    # Idempotency check: 0 new rows created, existing rows updated
    assert res2["telemetry_observations_created"] == 0
    assert res2["telemetry_observations_updated"] == 10

    obs_q2 = await db_session.execute(
        select(ResourceMetricObservation).where(
            ResourceMetricObservation.organization_id == org.id
        )
    )
    assert len(obs_q2.scalars().all()) == 10  # No duplicate rows created!


@pytest.mark.asyncio
async def test_telemetry_subsystem_independent_degradation(db_session):
    """Verifies that CloudWatch failure marks telemetry PARTIAL without failing the overall sync."""
    org = Organization(name="Degradation Org", slug="degradation-org")
    db_session.add(org)
    await db_session.commit()

    integration = Integration(
        org_id=org.id,
        provider_type="AWS",
        status="CONFIGURED",
        config_json={"role_arn": "arn:aws:iam::123456789012:role/AtlasReadOnlyRole", "region": "us-east-1"},
    )
    db_session.add(integration)
    await db_session.commit()

    factory = MagicMock(spec=AWSClientFactory)
    factory.role_arn = integration.config_json["role_arn"]
    factory.external_id = None
    factory.region_name = "us-east-1"

    mock_sts = MagicMock()
    mock_sts.get_caller_identity.return_value = {"Account": "123456789012", "Arn": factory.role_arn}

    mock_ec2 = MagicMock()
    mock_ec2.describe_regions.return_value = {"Regions": [{"RegionName": "us-east-1"}]}
    pag_ec2 = MagicMock()
    pag_ec2.paginate.return_value = [
        {"Reservations": [{"Instances": [{"InstanceId": "i-compute-99", "InstanceType": "t3.micro", "State": {"Name": "running"}}]}]}
    ]
    pag_ebs = MagicMock()
    pag_ebs.paginate.return_value = [{"Volumes": []}]
    mock_ec2.get_paginator.side_effect = lambda n: pag_ec2 if n == "describe_instances" else pag_ebs

    mock_ce = MagicMock()
    mock_ce.get_cost_and_usage.return_value = {"ResultsByTime": []}
    mock_ce.get_cost_and_usage_with_resources.return_value = {"ResultsByTime": []}

    # Mock CloudWatch failure with AccessDenied
    mock_cw = MagicMock()
    err = {"Error": {"Code": "AccessDeniedException", "Message": "No telemetry permissions"}}
    mock_cw.get_paginator.return_value.paginate.return_value = [{"Metrics": []}]
    mock_cw.get_metric_data.side_effect = ClientError(err, "GetMetricData")

    def _get_client(service, region=None):
        if service == "sts": return mock_sts
        if service == "ec2": return mock_ec2
        if service == "ce": return mock_ce
        if service == "cloudwatch": return mock_cw
        m = MagicMock()
        m.get_paginator.return_value.paginate.return_value = []
        return m

    factory.get_client.side_effect = _get_client

    res = await SyncCoordinator.execute_sync(
        session=db_session,
        integration_id=integration.id,
        org_id=org.id,
        client_factory=factory,
        target_end_date=date(2026, 9, 18),
    )

    # Sync status is PARTIAL, not fatal ERROR! Resources were still synced.
    assert res["status"] == "PARTIAL"
    assert res["resources_created"] == 1
    assert res["telemetry_status"] == "PARTIAL"
    assert any("CloudWatch" in w for w in res["warnings"])
