"""
NEXORA ATLAS - AWS RDS Read-Only Adapter
Discovers RDS database instances, clusters, and tags.
"""

import logging
from typing import List, Tuple, Optional
from botocore.exceptions import ClientError

from app.integrations.providers.base import (
    DiscoveredResource,
    DiscoveredTag,
)
from app.integrations.providers.aws.client import AWSClientFactory

logger = logging.getLogger("atlas.aws.rds")


class AWSRDSAdapter:
    """Read-only adapter for Amazon RDS."""

    def __init__(self, client_factory: AWSClientFactory):
        self.client_factory = client_factory

    def describe_db_instances(
        self,
        account_id: str,
        regions: Optional[List[str]] = None,
    ) -> Tuple[List[DiscoveredResource], List[DiscoveredTag], Optional[str]]:
        """
        Discovers RDS database instances across the specified regions.
        Returns: (resources, tags, failure_reason)
        """
        target_regions = regions or [self.client_factory.region_name]
        resources: List[DiscoveredResource] = []
        tags: List[DiscoveredTag] = []
        failure_reason: Optional[str] = None

        for reg in target_regions:
            try:
                rds_client = self.client_factory.get_client("rds", region=reg)
                paginator = rds_client.get_paginator("describe_db_instances")

                for page in paginator.paginate():
                    for db in page.get("DBInstances", []):
                        db_id = db.get("DBInstanceIdentifier")
                        if not db_id:
                            continue

                        arn = db.get("DBInstanceArn") or f"arn:aws:rds:{reg}:{account_id}:db:{db_id}"
                        status = db.get("DBInstanceStatus", "unknown").upper()
                        instance_class = db.get("DBInstanceClass", "db.t3.micro")
                        engine = db.get("Engine", "postgres")
                        engine_version = db.get("EngineVersion", "")
                        multi_az = db.get("MultiAZ", False)
                        allocated_storage = db.get("AllocatedStorage", 20)
                        storage_type = db.get("StorageType", "gp2")

                        # Tags
                        for t in db.get("TagList", []):
                            k, v = t.get("Key"), t.get("Value")
                            if k and v is not None:
                                tags.append(
                                    DiscoveredTag(
                                        resource_arn=arn,
                                        resource_native_id=db_id,
                                        key=k,
                                        value=v,
                                    )
                                )

                        specs = {
                            "instance_class": instance_class,
                            "instance_type": instance_class,  # Standardized key for headroom analysis
                            "engine": engine,
                            "engine_version": engine_version,
                            "multi_az": multi_az,
                            "allocated_storage": allocated_storage,
                            "storage_type": storage_type,
                            "status": status.lower(),
                        }

                        resources.append(
                            DiscoveredResource(
                                native_id=db_id,
                                arn=arn,
                                service_name="AmazonRDS",
                                resource_type="DATABASE",
                                region_code=reg,
                                name=db_id,
                                status=status,
                                specs_json=specs,
                            )
                        )

            except ClientError as e:
                code = e.response.get("Error", {}).get("Code", "Unknown")
                msg = e.response.get("Error", {}).get("Message", str(e))
                logger.warning("RDS discovery failed in %s: %s - %s", reg, code, msg)
                failure_reason = f"RDS {reg}: {code} - {msg}"
            except Exception as e:
                logger.warning("RDS discovery error in %s: %s", reg, str(e))
                failure_reason = f"RDS {reg}: {str(e)}"

        return resources, tags, failure_reason
