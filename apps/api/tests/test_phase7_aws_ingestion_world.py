"""
NEXORA ATLAS - Phase 7 Golden Integration Test
The Crown Jewel Ingestion Proof:
Mock AWS -> AWS Adapters -> Canonical Database -> Phase 5 Intelligence -> Phase 6 Analytics -> Scenarios & Portfolio.

Proves that AWS data does NOT require special intelligence logic.
The same deterministic intelligence and analytics engines operate identically
because the canonical Atlas data model is strictly maintained.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.account import CloudAccount, Integration
from app.models.resource import CloudResource
from app.models.cost import CostRecord
from app.services.tenant import TenantContext
from app.integrations.providers.aws.client import AWSClientFactory
from app.integrations.sync.coordinator import SyncCoordinator
from app.intelligence.orchestration.engine import IntelligenceEngine
from app.services.analytics import AnalyticsService


@pytest.mark.asyncio
async def test_golden_aws_ingestion_to_intelligence_and_analytics(db_session: AsyncSession):
    """
    Phase 7 Golden Test:
    Ingests real-world structured mock AWS infrastructure and 90-day billing history,
    then executes the Phase 5 and Phase 6 engines directly against the canonical database.
    """
    # 1. Setup Tenant Organization and Integration
    org = Organization(
        name="Acme Global Technologies",
        slug="acme-global",
        currency="USD",
        timezone="UTC",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    integration = Integration(
        org_id=org.id,
        provider_type="AWS",
        status="CONFIGURED",
        auth_method="IAM_ROLE",
        config_json={
            "role_arn": "arn:aws:iam::999988887777:role/AtlasReadOnlyProduction",
            "external_id": "acme-ext-id",
            "regions": ["us-east-1"],
            "account_name": "Production Workloads",
        },
    )
    db_session.add(integration)
    await db_session.commit()
    await db_session.refresh(integration)

    # 2. Build Rich Mock AWS Environment
    factory = MagicMock(spec=AWSClientFactory)
    factory.region_name = "us-east-1"
    factory.role_arn = "arn:aws:iam::999988887777:role/AtlasReadOnlyProduction"

    # STS
    mock_sts = MagicMock()
    mock_sts.get_caller_identity.return_value = {"Account": "999988887777"}

    # EC2 & EBS (Includes an oversized EC2 and an unattached EBS volume for Phase 5 to discover)
    mock_ec2 = MagicMock()
    mock_ec2.describe_regions.return_value = {"Regions": [{"RegionName": "us-east-1"}]}

    paginator_instances = MagicMock()
    paginator_instances.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-oversized-compute",
                            "InstanceType": "c5.4xlarge",
                            "State": {"Name": "running"},
                            "Architecture": "x86_64",
                            "PlatformDetails": "Linux/UNIX",
                            "CpuOptions": {"CoreCount": 8, "ThreadsPerCore": 2},
                            "Tags": [{"Key": "Name", "Value": "heavy-worker-01"}],
                        }
                    ]
                }
            ]
        }
    ]

    paginator_volumes = MagicMock()
    paginator_volumes.paginate.return_value = [
        {
            "Volumes": [
                {
                    "VolumeId": "vol-orphan-storage",
                    "Size": 500,
                    "VolumeType": "gp2",
                    "State": "available",
                    "Attachments": [],  # Unattached volume -> Waste Finding!
                    "Tags": [{"Key": "Name", "Value": "detached-data-volume"}],
                }
            ]
        }
    ]

    def _get_ec2_paginator(name):
        if name == "describe_instances":
            return paginator_instances
        if name == "describe_volumes":
            return paginator_volumes
        return MagicMock()

    mock_ec2.get_paginator.side_effect = _get_ec2_paginator

    # RDS (Idle database)
    mock_rds = MagicMock()
    paginator_rds = MagicMock()
    paginator_rds.paginate.return_value = [
        {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "dev-reporting-db",
                    "DBInstanceClass": "db.t3.medium",
                    "Engine": "postgres",
                    "DBInstanceStatus": "available",
                    "MultiAZ": False,
                    "AllocatedStorage": 100,
                    "StorageType": "gp2",
                    "TagList": [{"Key": "env", "Value": "dev"}],
                }
            ]
        }
    ]
    mock_rds.get_paginator.return_value = paginator_rds

    # S3
    mock_s3 = MagicMock()
    paginator_s3 = MagicMock()
    paginator_s3.paginate.return_value = [
        {"Buckets": [{"Name": "acme-log-archives", "CreationDate": None}]}
    ]
    mock_s3.get_paginator.return_value = paginator_s3
    mock_s3.head_bucket.return_value = {
        "ResponseMetadata": {"HTTPHeaders": {"x-amz-bucket-region": "us-east-1"}}
    }
    mock_s3.get_bucket_versioning.return_value = {"Status": "Disabled"}
    mock_s3.get_bucket_tagging.return_value = {"TagSet": []}

    # EKS
    mock_eks = MagicMock()
    paginator_eks = MagicMock()
    paginator_eks.paginate.return_value = [{"clusters": []}]
    mock_eks.get_paginator.return_value = paginator_eks

    # Cost Explorer (Generates 30 days of daily cost records)
    today = date(2026, 9, 15)
    start_date = today - timedelta(days=30)
    ce_results_by_time = []

    for i in range(30):
        day_date = start_date + timedelta(days=i)
        ce_results_by_time.append(
            {
                "TimePeriod": {
                    "Start": day_date.isoformat(),
                    "End": (day_date + timedelta(days=1)).isoformat(),
                },
                "Groups": [
                    {
                        "Keys": ["Amazon Elastic Compute Cloud - Compute", "BoxUsage:c5.4xlarge"],
                        "Metrics": {
                            "UnblendedCost": {"Amount": "180.0000", "Unit": "USD"},
                            "AmortizedCost": {"Amount": "180.0000", "Unit": "USD"},
                            "UsageQuantity": {"Amount": "24.0", "Unit": "Hrs"},
                        },
                    },
                    {
                        "Keys": ["Amazon Relational Database Service", "InstanceUsage:db.t3.medium"],
                        "Metrics": {
                            "UnblendedCost": {"Amount": "45.0000", "Unit": "USD"},
                            "AmortizedCost": {"Amount": "45.0000", "Unit": "USD"},
                            "UsageQuantity": {"Amount": "24.0", "Unit": "Hrs"},
                        },
                    },
                ],
            }
        )

    mock_ce = MagicMock()
    mock_ce.get_cost_and_usage.return_value = {"ResultsByTime": ce_results_by_time}
    ce_res_by_time = []
    for i in range(14):
        d = today - timedelta(days=i + 1)
        ce_res_by_time.append(
            {
                "TimePeriod": {
                    "Start": d.isoformat(),
                    "End": (d + timedelta(days=1)).isoformat(),
                },
                "Groups": [
                    {
                        "Keys": ["Amazon Elastic Compute Cloud - Compute", "i-oversized-compute"],
                        "Metrics": {
                            "UnblendedCost": {"Amount": "180.0000", "Unit": "USD"},
                            "AmortizedCost": {"Amount": "180.0000", "Unit": "USD"},
                        },
                    },
                    {
                        "Keys": ["Amazon Elastic Compute Cloud - Compute", "vol-orphan-storage"],
                        "Metrics": {
                            "UnblendedCost": {"Amount": "25.0000", "Unit": "USD"},
                            "AmortizedCost": {"Amount": "25.0000", "Unit": "USD"},
                        },
                    },
                ],
            }
        )
    mock_ce.get_cost_and_usage_with_resources.return_value = {"ResultsByTime": ce_res_by_time}

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
        return MagicMock()

    factory.get_client.side_effect = _get_client

    # 3. Execute Read-Only AWS Synchronization
    sync_result = await SyncCoordinator.execute_sync(
        session=db_session,
        integration_id=integration.id,
        org_id=org.id,
        client_factory=factory,
        target_end_date=today,
    )

    assert sync_result["status"] == "COMPLETED"
    assert sync_result["resources_created"] == 4  # EC2, EBS, RDS, S3
    assert sync_result["cost_records_created"] > 0

    # Attach synthetic telemetry onto the ingested resources to simulate cloudwatch/specs
    res_q = await db_session.execute(
        select(CloudResource).join(CloudAccount).where(CloudAccount.org_id == org.id)
    )
    for res in res_q.scalars().all():
        updated = dict(res.specs_json)
        if res.service_name == "AmazonEC2" and res.resource_type == "INSTANCE":
            updated["cpu_utilization_p95"] = 8.5
            updated["p95_cpu_utilization_pct"] = 8.5
            updated["instance_type"] = "c5.4xlarge"
            updated["memory_utilization_p95"] = 14.0
        elif res.service_name == "AmazonRDS":
            updated["avg_cpu_pct"] = 2.0
            updated["avg_connections"] = 0
            updated["status"] = "available"
        elif res.service_name == "AmazonEC2" and res.resource_type == "VOLUME":
            updated["volume_status"] = "available"
            updated["status"] = "available"
            updated["days_unattached"] = 15
            updated["attachment_count"] = 0
            updated["size_gb"] = 500
            updated["volume_type"] = "gp2"
        res.specs_json = updated

    await db_session.commit()

    # 4. PROOF A: Run Phase 5 Intelligence Engine on Ingested AWS Data
    intel_result = await IntelligenceEngine.run(db_session, organization_id=org.id)
    assert intel_result.ruleset_version == "atlas-intelligence-v1"
    assert intel_result.opportunities_found > 0
    assert intel_result.recommendations_generated > 0
    assert intel_result.potential_monthly_savings > Decimal("0.0000")

    # 5. PROOF B: Run Phase 6 Advanced Analytics on Ingested AWS Data
    acc_q = await db_session.execute(
        select(CloudAccount).where(CloudAccount.org_id == org.id)
    )
    acc = acc_q.scalars().first()

    tenant = TenantContext(
        org_id=org.id,
        org_name=org.name,
        slug=org.slug,
        currency="USD",
        timezone="UTC",
        is_demo=False,
        account_ids=[acc.id],
        accounts=[acc],
        account_name_map={acc.id: acc.name},
    )

    summary = await AnalyticsService.get_summary(db_session, tenant, comparison_window_days=14)

    # 6. Verify Progressive Chain of Reasoning outputs
    assert summary.trends is not None
    assert summary.drivers is not None
    assert summary.concentration is not None
    assert summary.efficiency is not None
    assert summary.portfolio is not None
    assert len(summary.scenarios) > 0

    # Verify Headroom calculated on real AWS compute instance
    ec2_headrooms = [h for h in summary.efficiency.headroom_items if h.service_name == "AmazonEC2"]
    assert len(ec2_headrooms) > 0
    assert ec2_headrooms[0].observed_utilization_headroom_cpu == Decimal("91.50")

    # Verify Financial Invariants
    for sim in summary.scenarios:
        assert (sim.baseline_monthly_cost - sim.projected_monthly_cost) == sim.monthly_savings
        assert sim.annual_savings == sim.monthly_savings * Decimal("12")
