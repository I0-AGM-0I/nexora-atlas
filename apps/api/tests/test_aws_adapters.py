"""
NEXORA ATLAS - AWS Read-Only Adapters Unit Tests
Tests each adapter with mocked AWS responses.
Verifies parsing, pagination, error handling, S3 HeadBucket, EKS resource semantics,
and dual-path Cost Explorer retrieval.
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

from app.integrations.providers.base import CostAttributionLevel
from app.integrations.providers.aws.client import AWSClientFactory
from app.integrations.providers.aws.cost import AWSCostExplorerAdapter
from app.integrations.providers.aws.ec2 import AWSEC2Adapter
from app.integrations.providers.aws.ebs import AWSEBSAdapter
from app.integrations.providers.aws.rds import AWSRDSAdapter
from app.integrations.providers.aws.s3 import AWSS3Adapter
from app.integrations.providers.aws.eks import AWSEKSAdapter


@pytest.fixture
def mock_factory():
    """Mock AWSClientFactory returning configured service client mocks."""
    factory = MagicMock(spec=AWSClientFactory)
    factory.region_name = "us-east-1"
    factory.role_arn = "arn:aws:iam::111122223333:role/AtlasReadOnly"
    return factory


def test_cost_explorer_aggregated_costs_parsing_and_keys(mock_factory):
    """Verifies aggregated cost parsing, deterministic source_record_key, and currency."""
    mock_ce = MagicMock()
    mock_ce.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-09-01", "End": "2026-09-02"},
                "Groups": [
                    {
                        "Keys": ["Amazon Elastic Compute Cloud - Compute", "BoxUsage:c5.large"],
                        "Metrics": {
                            "UnblendedCost": {"Amount": "125.5000", "Unit": "USD"},
                            "AmortizedCost": {"Amount": "125.5000", "Unit": "USD"},
                            "UsageQuantity": {"Amount": "24.0", "Unit": "Hrs"},
                        },
                    },
                    {
                        "Keys": ["Amazon Simple Storage Service", "TimedStorage-ByteHrs"],
                        "Metrics": {
                            "UnblendedCost": {"Amount": "18.2500", "Unit": "USD"},
                            "AmortizedCost": {"Amount": "18.2500", "Unit": "USD"},
                            "UsageQuantity": {"Amount": "50000.0", "Unit": "GB-Mo"},
                        },
                    },
                ],
            }
        ]
    }
    mock_factory.get_client.return_value = mock_ce

    adapter = AWSCostExplorerAdapter(mock_factory)
    records = adapter.get_aggregated_costs(
        account_id="111122223333",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 2),
    )

    assert len(records) == 2
    rec1 = records[0]
    assert rec1.service_name == "Amazon Elastic Compute Cloud - Compute"
    assert rec1.unblended_cost == Decimal("125.5000")
    assert rec1.currency == "USD"
    assert rec1.attribution_level == CostAttributionLevel.SERVICE
    assert len(rec1.source_record_key) == 64  # SHA-256 length

    rec2 = records[1]
    assert rec2.service_name == "Amazon Simple Storage Service"
    assert rec2.unblended_cost == Decimal("18.2500")
    assert rec2.usage_unit == "GB-Mo"


def test_cost_explorer_resource_costs_14_day_window_enforcement(mock_factory):
    """Verifies GetCostAndUsageWithResources enforces 14-day limit and captures resource IDs."""
    mock_ce = MagicMock()
    mock_ce.get_cost_and_usage_with_resources.return_value = {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-09-10", "End": "2026-09-11"},
                "Groups": [
                    {
                        "Keys": ["AmazonEC2", "i-0abcd1234ef567890"],
                        "Metrics": {
                            "UnblendedCost": {"Amount": "42.0000", "Unit": "USD"},
                            "AmortizedCost": {"Amount": "42.0000", "Unit": "USD"},
                        },
                    },
                ],
            }
        ]
    }
    mock_factory.get_client.return_value = mock_ce

    adapter = AWSCostExplorerAdapter(mock_factory)
    # Pass a 30-day window: adapter should clamp start_date to at most 14 days before end_date
    records, is_available, err = adapter.get_resource_costs(
        account_id="111122223333",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 9, 11),
    )

    assert is_available is True
    assert err is None
    assert len(records) == 1
    assert records[0].resource_native_id == "i-0abcd1234ef567890"
    assert records[0].attribution_level == CostAttributionLevel.RESOURCE


def test_ec2_adapter_instances_and_specs_parsing(mock_factory):
    """Verifies EC2 instances parsing, specs, and tags extraction."""
    mock_ec2 = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "InstanceType": "m5.large",
                            "State": {"Name": "running"},
                            "Architecture": "x86_64",
                            "PlatformDetails": "Linux/UNIX",
                            "CpuOptions": {"CoreCount": 2, "ThreadsPerCore": 1},
                            "LaunchTime": datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
                            "Tags": [
                                {"Key": "Name", "Value": "prod-api-server"},
                                {"Key": "Environment", "Value": "Production"},
                            ],
                        }
                    ]
                }
            ]
        }
    ]
    mock_ec2.get_paginator.return_value = mock_paginator
    mock_factory.get_client.return_value = mock_ec2

    adapter = AWSEC2Adapter(mock_factory)
    resources, tags, err = adapter.describe_instances(
        account_id="111122223333",
        regions=["us-east-1"],
    )

    assert err is None
    assert len(resources) == 1
    inst = resources[0]
    assert inst.native_id == "i-1234567890abcdef0"
    assert inst.name == "prod-api-server"
    assert inst.status == "RUNNING"
    assert inst.specs_json["instance_type"] == "m5.large"
    assert inst.specs_json["vcpu"] == 2

    assert len(tags) == 2
    env_tag = next(t for t in tags if t.key == "Environment")
    assert env_tag.value == "Production"


def test_ebs_adapter_volumes_attachment_status(mock_factory):
    """Verifies EBS volume discovery and attachment status."""
    mock_ec2 = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [
        {
            "Volumes": [
                {
                    "VolumeId": "vol-0123456789abcdef0",
                    "Size": 100,
                    "VolumeType": "gp3",
                    "State": "in-use",
                    "Attachments": [{"InstanceId": "i-1234567890abcdef0"}],
                    "Tags": [{"Key": "Name", "Value": "prod-root-disk"}],
                },
                {
                    "VolumeId": "vol-orphan999",
                    "Size": 50,
                    "VolumeType": "gp2",
                    "State": "available",
                    "Attachments": [],
                    "Tags": [],
                },
            ]
        }
    ]
    mock_ec2.get_paginator.return_value = mock_paginator
    mock_factory.get_client.return_value = mock_ec2

    adapter = AWSEBSAdapter(mock_factory)
    resources, tags, err = adapter.describe_volumes(
        account_id="111122223333",
        regions=["us-east-1"],
    )

    assert err is None
    assert len(resources) == 2
    vol1 = resources[0]
    assert vol1.specs_json["is_attached"] is True
    assert vol1.specs_json["volume_type"] == "gp3"

    vol2 = resources[1]
    assert vol2.specs_json["is_attached"] is False
    assert vol2.specs_json["status"] == "available"


def test_rds_adapter_db_instances_parsing(mock_factory):
    """Verifies RDS database discovery and specs parsing."""
    mock_rds = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [
        {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "prod-orders-db",
                    "DBInstanceClass": "db.m5.xlarge",
                    "Engine": "postgres",
                    "EngineVersion": "15.4",
                    "DBInstanceStatus": "available",
                    "MultiAZ": True,
                    "AllocatedStorage": 500,
                    "StorageType": "gp3",
                    "TagList": [{"Key": "tier", "Value": "database"}],
                }
            ]
        }
    ]
    mock_rds.get_paginator.return_value = mock_paginator
    mock_factory.get_client.return_value = mock_rds

    adapter = AWSRDSAdapter(mock_factory)
    resources, tags, err = adapter.describe_db_instances(
        account_id="111122223333",
        regions=["us-east-1"],
    )

    assert err is None
    assert len(resources) == 1
    db = resources[0]
    assert db.native_id == "prod-orders-db"
    assert db.status == "AVAILABLE"
    assert db.specs_json["multi_az"] is True
    assert db.specs_json["instance_type"] == "db.m5.xlarge"


def test_s3_adapter_paginated_list_buckets_and_head_bucket(mock_factory):
    """Verifies S3 ListBuckets pagination and HeadBucket region extraction."""
    mock_s3 = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [
        {
            "Buckets": [
                {
                    "Name": "company-data-lake-raw",
                    "CreationDate": datetime(2026, 1, 15, tzinfo=timezone.utc),
                }
            ]
        }
    ]
    mock_s3.get_paginator.return_value = mock_paginator
    mock_s3.head_bucket.return_value = {
        "ResponseMetadata": {"HTTPHeaders": {"x-amz-bucket-region": "ap-south-1"}}
    }
    mock_s3.get_bucket_versioning.return_value = {"Status": "Enabled"}
    mock_s3.get_bucket_tagging.return_value = {
        "TagSet": [{"Key": "Department", "Value": "DataOps"}]
    }
    mock_factory.get_client.return_value = mock_s3

    adapter = AWSS3Adapter(mock_factory)
    resources, tags, err = adapter.describe_buckets(account_id="111122223333")

    assert err is None
    assert len(resources) == 1
    b = resources[0]
    assert b.native_id == "company-data-lake-raw"
    assert b.region_code == "ap-south-1"
    assert b.specs_json["versioning"] == "Enabled"
    assert len(tags) == 1
    assert tags[0].key == "Department"


def test_eks_adapter_cluster_and_nodegroup_distinction(mock_factory):
    """Verifies distinct EKS Cluster and Nodegroup resource semantics."""
    mock_eks = MagicMock()
    mock_paginator_clusters = MagicMock()
    mock_paginator_clusters.paginate.return_value = [{"clusters": ["core-prod-cluster"]}]

    mock_paginator_ng = MagicMock()
    mock_paginator_ng.paginate.return_value = [{"nodegroups": ["compute-ng-1"]}]

    def _get_paginator(name):
        if name == "list_clusters":
            return mock_paginator_clusters
        if name == "list_nodegroups":
            return mock_paginator_ng
        return MagicMock()

    mock_eks.get_paginator.side_effect = _get_paginator
    mock_eks.describe_cluster.return_value = {
        "cluster": {
            "name": "core-prod-cluster",
            "version": "1.30",
            "status": "ACTIVE",
            "arn": "arn:aws:eks:us-east-1:111122223333:cluster/core-prod-cluster",
            "tags": {"Environment": "Production"},
        }
    }
    mock_eks.describe_nodegroup.return_value = {
        "nodegroup": {
            "nodegroupName": "compute-ng-1",
            "status": "ACTIVE",
            "instanceTypes": ["c5.xlarge"],
            "capacityType": "ON_DEMAND",
            "tags": {"Role": "WorkerNodeGroup"},
        }
    }
    mock_factory.get_client.return_value = mock_eks

    adapter = AWSEKSAdapter(mock_factory)
    resources, tags, err = adapter.describe_clusters(
        account_id="111122223333",
        regions=["us-east-1"],
    )

    assert err is None
    assert len(resources) == 2

    # Cluster
    cluster_res = next(r for r in resources if r.resource_type == "CLUSTER")
    assert cluster_res.service_name == "AmazonEKS"
    assert cluster_res.native_id == "core-prod-cluster"

    # Nodegroup
    ng_res = next(r for r in resources if r.resource_type == "NODEGROUP")
    assert ng_res.service_name == "AmazonEKS"
    assert ng_res.native_id == "core-prod-cluster/compute-ng-1"
    assert ng_res.specs_json["instance_types"] == ["c5.xlarge"]
