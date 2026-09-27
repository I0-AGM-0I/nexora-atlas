"""
NEXORA ATLAS - AWS EBS Read-Only Adapter
Discovers EBS volumes and attached/unattached status.
"""

import logging
from typing import List, Tuple, Optional
from botocore.exceptions import ClientError

from app.integrations.providers.base import (
    DiscoveredResource,
    DiscoveredTag,
)
from app.integrations.providers.aws.client import AWSClientFactory

logger = logging.getLogger("atlas.aws.ebs")


class AWSEBSAdapter:
    """Read-only adapter for Amazon EBS Volumes."""

    def __init__(self, client_factory: AWSClientFactory):
        self.client_factory = client_factory

    def describe_volumes(
        self,
        account_id: str,
        regions: Optional[List[str]] = None,
    ) -> Tuple[List[DiscoveredResource], List[DiscoveredTag], Optional[str]]:
        """
        Discovers EBS volumes across the specified regions.
        Returns: (resources, tags, failure_reason)
        """
        target_regions = regions or [self.client_factory.region_name]
        resources: List[DiscoveredResource] = []
        tags: List[DiscoveredTag] = []
        failure_reason: Optional[str] = None

        for reg in target_regions:
            try:
                ec2_client = self.client_factory.get_client("ec2", region=reg)
                paginator = ec2_client.get_paginator("describe_volumes")

                for page in paginator.paginate():
                    for vol in page.get("Volumes", []):
                        vol_id = vol.get("VolumeId")
                        if not vol_id:
                            continue

                        arn = f"arn:aws:ec2:{reg}:{account_id}:volume/{vol_id}"
                        state = vol.get("State", "unknown").upper()
                        vol_type = vol.get("VolumeType", "gp2")
                        size_gb = vol.get("Size", 0)
                        iops = vol.get("Iops")
                        throughput = vol.get("Throughput")
                        encrypted = vol.get("Encrypted", False)
                        attachments = vol.get("Attachments", [])

                        # Tags
                        vol_name = None
                        for t in vol.get("Tags", []):
                            k, v = t.get("Key"), t.get("Value")
                            if k and v is not None:
                                if k.lower() == "name":
                                    vol_name = v
                                tags.append(
                                    DiscoveredTag(
                                        resource_arn=arn,
                                        resource_native_id=vol_id,
                                        key=k,
                                        value=v,
                                    )
                                )

                        specs = {
                            "size_gb": size_gb,
                            "volume_type": vol_type,
                            "iops": iops,
                            "throughput": throughput,
                            "encrypted": encrypted,
                            "attachment_count": len(attachments),
                            "is_attached": len(attachments) > 0,
                            "status": "in-use" if attachments else "available",
                        }

                        resources.append(
                            DiscoveredResource(
                                native_id=vol_id,
                                arn=arn,
                                service_name="AmazonEC2",
                                resource_type="VOLUME",
                                region_code=reg,
                                name=vol_name or vol_id,
                                status=state,
                                specs_json=specs,
                            )
                        )

            except ClientError as e:
                code = e.response.get("Error", {}).get("Code", "Unknown")
                msg = e.response.get("Error", {}).get("Message", str(e))
                logger.warning("EBS discovery failed in %s: %s - %s", reg, code, msg)
                failure_reason = f"EBS {reg}: {code} - {msg}"
            except Exception as e:
                logger.warning("EBS discovery error in %s: %s", reg, str(e))
                failure_reason = f"EBS {reg}: {str(e)}"

        return resources, tags, failure_reason
