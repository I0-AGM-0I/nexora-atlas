"""
NEXORA ATLAS - Authoritative-Only Resource Disappearance Tests
Verifies Correction 8 & 16:
1. Sync 1-2: EC2 instances A, B, C are ACTIVE.
2. Sync 3: Authoritative EC2 pass succeeds with only A and B -> C transitions to TERMINATED.
3. Sync 4: EC2 pass fails or is partial -> existing resources are NOT marked terminated.
"""

import pytest
from datetime import date
from unittest.mock import MagicMock
from botocore.exceptions import ClientError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.account import CloudAccount, Integration
from app.models.resource import CloudResource
from app.integrations.providers.aws.client import AWSClientFactory
from app.integrations.sync.coordinator import SyncCoordinator


@pytest.mark.asyncio
async def test_authoritative_disappearance_vs_partial_failure(db_session: AsyncSession):
    """
    Verifies that resources only transition to TERMINATED after a successful
    authoritative inventory pass, and never due to partial or failing passes.
    """
    org = Organization(
        name="Disappearance Test Org",
        slug="disappear-test-org",
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
        config_json={"role_arn": "arn:aws:iam::111122223333:role/AtlasReadOnly"},
    )
    db_session.add(integration)
    await db_session.commit()
    await db_session.refresh(integration)

    # Setup base mock factory
    factory = MagicMock(spec=AWSClientFactory)
    factory.region_name = "us-east-1"
    factory.role_arn = "arn:aws:iam::111122223333:role/AtlasReadOnly"

    mock_sts = MagicMock()
    mock_sts.get_caller_identity.return_value = {"Account": "111122223333"}

    mock_ce = MagicMock()
    mock_ce.get_cost_and_usage.return_value = {"ResultsByTime": []}
    mock_ce.get_cost_and_usage_with_resources.return_value = {"ResultsByTime": []}

    mock_rds = MagicMock()
    mock_rds.get_paginator.return_value.paginate.return_value = []

    mock_s3 = MagicMock()
    mock_s3.get_paginator.return_value.paginate.return_value = []

    mock_eks = MagicMock()
    mock_eks.get_paginator.return_value.paginate.return_value = []

    # =========================================================================
    # STEP 1: Sync 1 with Instances A, B, C
    # =========================================================================
    mock_ec2_1 = MagicMock()
    mock_ec2_1.describe_regions.return_value = {"Regions": [{"RegionName": "us-east-1"}]}
    paginator_1 = MagicMock()
    paginator_1.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {"InstanceId": "i-inst-A", "InstanceType": "t3.micro", "State": {"Name": "running"}},
                        {"InstanceId": "i-inst-B", "InstanceType": "t3.micro", "State": {"Name": "running"}},
                        {"InstanceId": "i-inst-C", "InstanceType": "t3.micro", "State": {"Name": "running"}},
                    ]
                }
            ]
        }
    ]
    paginator_ebs_empty = MagicMock()
    paginator_ebs_empty.paginate.return_value = []

    def _get_ec2_p1(name):
        if name == "describe_instances":
            return paginator_1
        return paginator_ebs_empty

    mock_ec2_1.get_paginator.side_effect = _get_ec2_p1

    def _get_client_step1(service_name, region=None):
        if service_name == "sts":
            return mock_sts
        if service_name == "ec2":
            return mock_ec2_1
        if service_name == "ce":
            return mock_ce
        if service_name == "rds":
            return mock_rds
        if service_name == "s3":
            return mock_s3
        if service_name == "eks":
            return mock_eks
        return MagicMock()

    factory.get_client.side_effect = _get_client_step1

    res_1 = await SyncCoordinator.execute_sync(
        session=db_session,
        integration_id=integration.id,
        org_id=org.id,
        client_factory=factory,
        target_end_date=date(2026, 9, 2),
    )
    assert res_1["status"] == "COMPLETED"

    # Verify all 3 are ACTIVE
    inst_q = await db_session.execute(
        select(CloudResource).where(CloudResource.service_name == "AmazonEC2")
    )
    instances = {i.native_id: i for i in inst_q.scalars().all()}
    assert len(instances) == 3
    assert instances["i-inst-A"].status == "RUNNING"
    assert instances["i-inst-B"].status == "RUNNING"
    assert instances["i-inst-C"].status == "RUNNING"

    # =========================================================================
    # STEP 2: Sync 3 (Authoritative EC2 pass succeeds with only A and B)
    # i-inst-C must transition to TERMINATED!
    # =========================================================================
    mock_ec2_2 = MagicMock()
    mock_ec2_2.describe_regions.return_value = {"Regions": [{"RegionName": "us-east-1"}]}
    paginator_2 = MagicMock()
    paginator_2.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {"InstanceId": "i-inst-A", "InstanceType": "t3.micro", "State": {"Name": "running"}},
                        {"InstanceId": "i-inst-B", "InstanceType": "t3.micro", "State": {"Name": "running"}},
                        # i-inst-C is absent
                    ]
                }
            ]
        }
    ]

    def _get_ec2_p2(name):
        if name == "describe_instances":
            return paginator_2
        return paginator_ebs_empty

    mock_ec2_2.get_paginator.side_effect = _get_ec2_p2

    def _get_client_step2(service_name, region=None):
        if service_name == "sts":
            return mock_sts
        if service_name == "ec2":
            return mock_ec2_2
        if service_name == "ce":
            return mock_ce
        if service_name == "rds":
            return mock_rds
        if service_name == "s3":
            return mock_s3
        if service_name == "eks":
            return mock_eks
        return MagicMock()

    factory.get_client.side_effect = _get_client_step2

    res_2 = await SyncCoordinator.execute_sync(
        session=db_session,
        integration_id=integration.id,
        org_id=org.id,
        client_factory=factory,
        target_end_date=date(2026, 9, 2),
    )
    assert res_2["status"] == "COMPLETED"

    # Verify i-inst-C transitioned to TERMINATED
    await db_session.commit()
    inst_q2 = await db_session.execute(
        select(CloudResource).where(CloudResource.service_name == "AmazonEC2")
    )
    instances_2 = {i.native_id: i for i in inst_q2.scalars().all()}
    assert instances_2["i-inst-A"].status == "RUNNING"
    assert instances_2["i-inst-B"].status == "RUNNING"
    assert instances_2["i-inst-C"].status == "TERMINATED"

    # =========================================================================
    # STEP 3: Sync 4 (EC2 adapter encounters an error or partial failure)
    # Remaining instances (A and B) must NOT be marked terminated!
    # =========================================================================
    mock_ec2_3 = MagicMock()
    mock_ec2_3.describe_regions.return_value = {"Regions": [{"RegionName": "us-east-1"}]}
    mock_ec2_3.get_paginator.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Access Denied on EC2"}},
        "DescribeInstances",
    )

    def _get_client_step3(service_name, region=None):
        if service_name == "sts":
            return mock_sts
        if service_name == "ec2":
            return mock_ec2_3
        if service_name == "ce":
            return mock_ce
        if service_name == "rds":
            return mock_rds
        if service_name == "s3":
            return mock_s3
        if service_name == "eks":
            return mock_eks
        return MagicMock()

    factory.get_client.side_effect = _get_client_step3

    res_3 = await SyncCoordinator.execute_sync(
        session=db_session,
        integration_id=integration.id,
        org_id=org.id,
        client_factory=factory,
        target_end_date=date(2026, 9, 2),
    )
    # Job should be marked PARTIAL because EC2 failed
    assert res_3["status"] == "PARTIAL"

    # Existing resources must NOT be corrupted or falsely marked terminated
    await db_session.commit()
    inst_q3 = await db_session.execute(
        select(CloudResource).where(CloudResource.service_name == "AmazonEC2")
    )
    instances_3 = {i.native_id: i for i in inst_q3.scalars().all()}
    assert instances_3["i-inst-A"].status == "RUNNING"
    assert instances_3["i-inst-B"].status == "RUNNING"
    assert instances_3["i-inst-C"].status == "TERMINATED"
