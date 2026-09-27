"""
NEXORA ATLAS - AWS Authentication & Bounded Permission Probe
Validates customer IAM role assumption and probes service-level read-only permissions
using lightweight, bounded checks (zero whole-inventory scans).
"""

import logging
from datetime import date, timedelta
from typing import Optional
from botocore.exceptions import ClientError

from app.integrations.providers.base import (
    ConnectionValidationResult,
    AWSServicePermissions,
    PermissionStatus,
)
from app.integrations.providers.aws.client import AWSClientFactory

logger = logging.getLogger("atlas.aws.auth")


class AWSAuthenticator:
    """Performs lightweight connection validation and permission probing."""

    @classmethod
    def validate_connection(
        cls,
        client_factory: AWSClientFactory,
    ) -> ConnectionValidationResult:
        """
        Validates AWS IAM connection:
        1. Calls STS GetCallerIdentity to verify role and account ID.
        2. Probes minimal representative endpoints with limit=1 to determine capability availability.
        3. Returns sanitized ConnectionValidationResult.
        """
        role_arn = client_factory.role_arn
        masked_arn = None
        if role_arn:
            parts = role_arn.split(":")
            if len(parts) >= 6:
                # e.g. arn:aws:iam::123456789012:role/AtlasReadOnly -> arn:aws:iam::***:role/AtlasReadOnly
                parts[4] = "***"
                masked_arn = ":".join(parts)
            else:
                masked_arn = f"...{role_arn[-15:]}"

        # 1. STS Caller Identity
        account_id: Optional[str] = None
        try:
            sts_client = client_factory.get_client("sts")
            identity = sts_client.get_caller_identity()
            account_id = identity.get("Account")
        except Exception as e:
            logger.warning("STS GetCallerIdentity failed: %s", str(e))
            return ConnectionValidationResult(
                is_valid=False,
                account_id=None,
                region=client_factory.region_name,
                role_arn_masked=masked_arn,
                permissions=AWSServicePermissions(),
                error_message=f"Authentication failed: {str(e)}",
            )

        permissions = AWSServicePermissions()

        # 2. Probe Cost Explorer - Aggregated (ce:GetCostAndUsage)
        try:
            ce_client = client_factory.get_client("ce", region="us-east-1")
            today = date.today()
            ce_client.get_cost_and_usage(
                TimePeriod={
                    "Start": (today - timedelta(days=2)).isoformat(),
                    "End": (today - timedelta(days=1)).isoformat(),
                },
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
            )
            permissions.cost_aggregated = PermissionStatus.AVAILABLE
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            logger.info("Cost Explorer aggregated probe result: %s", code)
            permissions.cost_aggregated = (
                PermissionStatus.DENIED if "AccessDenied" in code else PermissionStatus.AVAILABLE
            )
        except Exception:
            permissions.cost_aggregated = PermissionStatus.DENIED

        # 3. Probe Cost Explorer - Resource-Level (ce:GetCostAndUsageWithResources)
        try:
            ce_client = client_factory.get_client("ce", region="us-east-1")
            today = date.today()
            ce_client.get_cost_and_usage_with_resources(
                TimePeriod={
                    "Start": (today - timedelta(days=2)).isoformat(),
                    "End": (today - timedelta(days=1)).isoformat(),
                },
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
                Filter={"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Elastic Compute Cloud - Compute"]}},
            )
            permissions.cost_resource_level = PermissionStatus.AVAILABLE
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            logger.info("Cost Explorer resource-level probe result: %s", code)
            permissions.cost_resource_level = PermissionStatus.DENIED
        except Exception:
            permissions.cost_resource_level = PermissionStatus.DENIED

        # 4. Probe EC2 Instances (ec2:DescribeInstances with MaxResults=5)
        try:
            ec2_client = client_factory.get_client("ec2")
            ec2_client.describe_instances(MaxResults=5)
            permissions.ec2_inventory = PermissionStatus.AVAILABLE
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            permissions.ec2_inventory = (
                PermissionStatus.DENIED if "AccessDenied" in code or "Unauthorized" in code else PermissionStatus.AVAILABLE
            )
        except Exception:
            permissions.ec2_inventory = PermissionStatus.DENIED

        # 5. Probe EBS Volumes (ec2:DescribeVolumes with MaxResults=5)
        try:
            ec2_client = client_factory.get_client("ec2")
            ec2_client.describe_volumes(MaxResults=5)
            permissions.ebs_inventory = PermissionStatus.AVAILABLE
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            permissions.ebs_inventory = (
                PermissionStatus.DENIED if "AccessDenied" in code or "Unauthorized" in code else PermissionStatus.AVAILABLE
            )
        except Exception:
            permissions.ebs_inventory = PermissionStatus.DENIED

        # 6. Probe RDS (rds:DescribeDBInstances with MaxRecords=20)
        try:
            rds_client = client_factory.get_client("rds")
            rds_client.describe_db_instances(MaxRecords=20)
            permissions.rds_inventory = PermissionStatus.AVAILABLE
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            permissions.rds_inventory = (
                PermissionStatus.DENIED if "AccessDenied" in code else PermissionStatus.AVAILABLE
            )
        except Exception:
            permissions.rds_inventory = PermissionStatus.DENIED

        # 7. Probe S3 (s3:ListBuckets paginated single page)
        try:
            s3_client = client_factory.get_client("s3")
            paginator = s3_client.get_paginator("list_buckets")
            # Pull first page only
            for page in paginator.paginate(PaginationConfig={"MaxItems": 1}):
                break
            permissions.s3_inventory = PermissionStatus.AVAILABLE
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            permissions.s3_inventory = (
                PermissionStatus.DENIED if "AccessDenied" in code else PermissionStatus.AVAILABLE
            )
        except Exception:
            permissions.s3_inventory = PermissionStatus.DENIED

        # 8. Probe EKS (eks:ListClusters with maxResults=1)
        try:
            eks_client = client_factory.get_client("eks")
            eks_client.list_clusters(maxResults=1)
            permissions.eks_inventory = PermissionStatus.AVAILABLE
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            permissions.eks_inventory = (
                PermissionStatus.DENIED if "AccessDenied" in code else PermissionStatus.AVAILABLE
            )
        except Exception:
            permissions.eks_inventory = PermissionStatus.DENIED

        # 9. Probe CloudWatch (cloudwatch:ListMetrics with MaxRecords=1)
        try:
            cw_client = client_factory.get_client("cloudwatch")
            paginator_cw = cw_client.get_paginator("list_metrics")
            for page in paginator_cw.paginate(PaginationConfig={"MaxItems": 1}):
                break
            permissions.cloudwatch_telemetry = PermissionStatus.AVAILABLE
            # Granular capabilities inherit from service inventory + CW access
            permissions.ec2_cpu_telemetry = (
                PermissionStatus.AVAILABLE if permissions.ec2_inventory == PermissionStatus.AVAILABLE else PermissionStatus.NOT_CONFIGURED
            )
            permissions.rds_cpu_telemetry = (
                PermissionStatus.AVAILABLE if permissions.rds_inventory == PermissionStatus.AVAILABLE else PermissionStatus.NOT_CONFIGURED
            )
            permissions.ebs_io_telemetry = (
                PermissionStatus.AVAILABLE if permissions.ebs_inventory == PermissionStatus.AVAILABLE else PermissionStatus.NOT_CONFIGURED
            )
            permissions.s3_telemetry = PermissionStatus.NOT_CONFIGURED
            permissions.eks_telemetry = PermissionStatus.NOT_CONFIGURED
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            is_denied = "AccessDenied" in code
            status = PermissionStatus.DENIED if is_denied else PermissionStatus.NOT_CONFIGURED
            permissions.cloudwatch_telemetry = status
            permissions.ec2_cpu_telemetry = status
            permissions.rds_cpu_telemetry = status
            permissions.ebs_io_telemetry = status
            permissions.s3_telemetry = PermissionStatus.NOT_CONFIGURED
            permissions.eks_telemetry = PermissionStatus.NOT_CONFIGURED
        except Exception:
            permissions.cloudwatch_telemetry = PermissionStatus.DENIED
            permissions.ec2_cpu_telemetry = PermissionStatus.DENIED
            permissions.rds_cpu_telemetry = PermissionStatus.DENIED
            permissions.ebs_io_telemetry = PermissionStatus.DENIED
            permissions.s3_telemetry = PermissionStatus.NOT_CONFIGURED
            permissions.eks_telemetry = PermissionStatus.NOT_CONFIGURED

        # Connection is valid if STS succeeded and at least one core service is available
        is_valid = bool(
            account_id
            and (
                permissions.cost_aggregated == PermissionStatus.AVAILABLE
                or permissions.ec2_inventory == PermissionStatus.AVAILABLE
                or permissions.rds_inventory == PermissionStatus.AVAILABLE
            )
        )

        return ConnectionValidationResult(
            is_valid=is_valid,
            account_id=account_id,
            region=client_factory.region_name,
            role_arn_masked=masked_arn,
            permissions=permissions,
            error_message=None if is_valid else "IAM role assumed but essential permissions were denied.",
        )
