"""
NEXORA ATLAS - AWS EC2 Read-Only Adapter
Discovers regions, EC2 instances, and tags.
"""

import logging
from typing import List, Tuple, Optional
from botocore.exceptions import ClientError

from app.integrations.providers.base import (
    DiscoveredRegion,
    DiscoveredResource,
    DiscoveredTag,
)
from app.integrations.providers.aws.client import AWSClientFactory

logger = logging.getLogger("atlas.aws.ec2")


class AWSEC2Adapter:
    """Read-only adapter for Amazon EC2."""

    def __init__(self, client_factory: AWSClientFactory):
        self.client_factory = client_factory

    def describe_regions(self) -> List[DiscoveredRegion]:
        """Discovers available AWS regions."""
        ec2_client = self.client_factory.get_client("ec2")
        try:
            response = AWSClientFactory.execute_with_retry(
                "DescribeRegions",
                ec2_client.describe_regions,
                AllRegions=False,
            )
            regions = []
            for r in response.get("Regions", []):
                code = r.get("RegionName")
                if code:
                    regions.append(
                        DiscoveredRegion(
                            region_code=code,
                            display_name=r.get("OptInStatus", code),
                            provider_type="AWS",
                        )
                    )
            return regions
        except Exception as e:
            logger.warning("Failed to describe EC2 regions: %s", str(e))
            # Fallback to standard primary regions
            return [
                DiscoveredRegion(region_code="us-east-1", display_name="US East (N. Virginia)", provider_type="AWS"),
                DiscoveredRegion(region_code="ap-south-1", display_name="Asia Pacific (Mumbai)", provider_type="AWS"),
            ]

    def describe_instances(
        self,
        account_id: str,
        regions: Optional[List[str]] = None,
    ) -> Tuple[List[DiscoveredResource], List[DiscoveredTag], Optional[str]]:
        """
        Discovers EC2 instances across the specified regions.
        Returns: (resources, tags, failure_reason)
        """
        target_regions = regions or [self.client_factory.region_name]
        resources: List[DiscoveredResource] = []
        tags: List[DiscoveredTag] = []
        failure_reason: Optional[str] = None

        for reg in target_regions:
            try:
                ec2_client = self.client_factory.get_client("ec2", region=reg)
                paginator = ec2_client.get_paginator("describe_instances")

                for page in paginator.paginate():
                    for reservation in page.get("Reservations", []):
                        for inst in reservation.get("Instances", []):
                            inst_id = inst.get("InstanceId")
                            if not inst_id:
                                continue

                            arn = f"arn:aws:ec2:{reg}:{account_id}:instance/{inst_id}"
                            state_name = inst.get("State", {}).get("Name", "unknown").upper()
                            inst_type = inst.get("InstanceType", "unknown")
                            arch = inst.get("Architecture", "x86_64")
                            platform = inst.get("PlatformDetails", "Linux/UNIX")
                            cpu_options = inst.get("CpuOptions", {})
                            core_count = cpu_options.get("CoreCount")
                            threads_per_core = cpu_options.get("ThreadsPerCore")
                            vcpu = (
                                (core_count * threads_per_core)
                                if (core_count and threads_per_core)
                                else None
                            )

                            # Tags
                            inst_name = None
                            for t in inst.get("Tags", []):
                                k, v = t.get("Key"), t.get("Value")
                                if k and v is not None:
                                    if k.lower() == "name":
                                        inst_name = v
                                    tags.append(
                                        DiscoveredTag(
                                            resource_arn=arn,
                                            resource_native_id=inst_id,
                                            key=k,
                                            value=v,
                                        )
                                    )

                            specs = {
                                "instance_type": inst_type,
                                "architecture": arch,
                                "platform": platform,
                                "vcpu": vcpu,
                                "launch_time": inst.get("LaunchTime").isoformat() if inst.get("LaunchTime") else None,
                            }

                            resources.append(
                                DiscoveredResource(
                                    native_id=inst_id,
                                    arn=arn,
                                    service_name="AmazonEC2",
                                    resource_type="INSTANCE",
                                    region_code=reg,
                                    name=inst_name or inst_id,
                                    status=state_name,
                                    specs_json=specs,
                                )
                            )

            except ClientError as e:
                code = e.response.get("Error", {}).get("Code", "Unknown")
                msg = e.response.get("Error", {}).get("Message", str(e))
                logger.warning("EC2 discovery failed in %s: %s - %s", reg, code, msg)
                failure_reason = f"EC2 {reg}: {code} - {msg}"
            except Exception as e:
                logger.warning("EC2 discovery error in %s: %s", reg, str(e))
                failure_reason = f"EC2 {reg}: {str(e)}"

        return resources, tags, failure_reason
