"""
NEXORA ATLAS - Cost Explorer Capability Degradation Tests
Verifies Correction 17:
When Aggregated Cost Explorer is available but Resource-level Cost Explorer is denied,
Atlas successfully ingests 90-day service/account financial data and reports resource-level
attribution as unavailable without crashing or failing the job.
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from botocore.exceptions import ClientError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.account import CloudAccount, Integration
from app.models.cost import CostRecord
from app.integrations.providers.base import CostAttributionLevel
from app.integrations.providers.aws.client import AWSClientFactory
from app.integrations.providers.aws.cost import AWSCostExplorerAdapter
from app.integrations.sync.coordinator import SyncCoordinator


def test_cost_explorer_degradation_isolated_adapter():
    """Verifies that AWSCostExplorerAdapter returns is_available=False gracefully when denied."""
    mock_factory = MagicMock(spec=AWSClientFactory)
    mock_factory.region_name = "us-east-1"
    mock_ce = MagicMock()

    # GetCostAndUsage succeeds
    mock_ce.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-09-01", "End": "2026-09-02"},
                "Groups": [
                    {
                        "Keys": ["AmazonEC2", "BoxUsage:t3.medium"],
                        "Metrics": {
                            "UnblendedCost": {"Amount": "50.0000", "Unit": "USD"},
                            "AmortizedCost": {"Amount": "50.0000", "Unit": "USD"},
                        },
                    }
                ],
            }
        ]
    }

    # GetCostAndUsageWithResources fails with AccessDenied
    mock_ce.get_cost_and_usage_with_resources.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "Opt-in resource level CE required"}},
        "GetCostAndUsageWithResources",
    )

    mock_factory.get_client.return_value = mock_ce
    adapter = AWSCostExplorerAdapter(mock_factory)

    # 1. Aggregated costs succeed
    agg_records = adapter.get_aggregated_costs("111122223333", date(2026, 9, 1), date(2026, 9, 2))
    assert len(agg_records) == 1
    assert agg_records[0].unblended_cost == Decimal("50.0000")

    # 2. Resource-level costs fail gracefully
    res_records, is_avail, err = adapter.get_resource_costs("111122223333", date(2026, 9, 1), date(2026, 9, 2))
    assert is_avail is False
    assert len(res_records) == 0
    assert "Opt-in resource level CE required" in str(err) or "AccessDenied" in str(err)


@pytest.mark.asyncio
async def test_sync_coordinator_degradation_behavior(db_session: AsyncSession):
    """
    Verifies that SyncCoordinator completes successfully with service-level attribution
    when resource-level CE is denied.
    """
    org = Organization(
        name="Degradation Test Org",
        slug="deg-test-org",
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

    factory = MagicMock(spec=AWSClientFactory)
    factory.region_name = "us-east-1"
    factory.role_arn = "arn:aws:iam::111122223333:role/AtlasReadOnly"

    mock_sts = MagicMock()
    mock_sts.get_caller_identity.return_value = {"Account": "111122223333"}

    mock_ec2 = MagicMock()
    mock_ec2.describe_regions.return_value = {"Regions": [{"RegionName": "us-east-1"}]}
    mock_ec2.get_paginator.return_value.paginate.return_value = []

    mock_rds = MagicMock()
    mock_rds.get_paginator.return_value.paginate.return_value = []

    mock_s3 = MagicMock()
    mock_s3.get_paginator.return_value.paginate.return_value = []

    mock_eks = MagicMock()
    mock_eks.get_paginator.return_value.paginate.return_value = []

    mock_ce = MagicMock()
    mock_ce.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-09-01", "End": "2026-09-02"},
                "Groups": [
                    {
                        "Keys": ["AmazonEC2", "BoxUsage:t3.medium"],
                        "Metrics": {
                            "UnblendedCost": {"Amount": "95.0000", "Unit": "USD"},
                            "AmortizedCost": {"Amount": "95.0000", "Unit": "USD"},
                        },
                    }
                ],
            }
        ]
    }
    # Denied resource-level
    mock_ce.get_cost_and_usage_with_resources.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Resource CE denied"}},
        "GetCostAndUsageWithResources",
    )

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

    res = await SyncCoordinator.execute_sync(
        session=db_session,
        integration_id=integration.id,
        org_id=org.id,
        client_factory=factory,
        target_end_date=date(2026, 9, 2),
    )

    # Ingestion should succeed (aggregated costs processed)
    assert res["cost_records_processed"] == 1
    assert res["cost_records_created"] == 1

    # Database records must have null resource_id and service-level attribution
    acc_q = await db_session.execute(
        select(CloudAccount).where(CloudAccount.org_id == org.id)
    )
    acc = acc_q.scalars().first()
    cost_records = (
        await db_session.execute(
            select(CostRecord).where(CostRecord.account_id == acc.id)
        )
    ).scalars().all()

    assert len(cost_records) == 1
    assert cost_records[0].unblended_cost == Decimal("95.0000")
    assert cost_records[0].resource_id is None
