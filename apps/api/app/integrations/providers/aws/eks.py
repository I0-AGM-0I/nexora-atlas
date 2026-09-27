"""
NEXORA ATLAS - AWS EKS Read-Only Adapter
Discovers EKS clusters and managed nodegroups with distinct resource semantics.
Strictly distinguishes EKS Clusters from compute worker nodes.
"""

import logging
from typing import List, Tuple, Optional
from botocore.exceptions import ClientError

from app.integrations.providers.base import (
    DiscoveredResource,
    DiscoveredTag,
)
from app.integrations.providers.aws.client import AWSClientFactory

logger = logging.getLogger("atlas.aws.eks")


class AWSEKSAdapter:
    """Read-only adapter for Amazon EKS."""

    def __init__(self, client_factory: AWSClientFactory):
        self.client_factory = client_factory

    def describe_clusters(
        self,
        account_id: str,
        regions: Optional[List[str]] = None,
    ) -> Tuple[List[DiscoveredResource], List[DiscoveredTag], Optional[str]]:
        """
        Discovers EKS clusters and their managed node groups across regions.
        Returns: (resources, tags, failure_reason)
        """
        target_regions = regions or [self.client_factory.region_name]
        resources: List[DiscoveredResource] = []
        tags: List[DiscoveredTag] = []
        failure_reason: Optional[str] = None

        for reg in target_regions:
            try:
                eks_client = self.client_factory.get_client("eks", region=reg)
                paginator = eks_client.get_paginator("list_clusters")

                for page in paginator.paginate():
                    for cluster_name in page.get("clusters", []):
                        # Describe Cluster
                        try:
                            c_res = eks_client.describe_cluster(name=cluster_name)
                            cluster = c_res.get("cluster", {})
                            arn = cluster.get("arn") or f"arn:aws:eks:{reg}:{account_id}:cluster/{cluster_name}"
                            version = cluster.get("version", "")
                            status = cluster.get("status", "ACTIVE").upper()

                            # Cluster Tags
                            for k, v in cluster.get("tags", {}).items():
                                tags.append(
                                    DiscoveredTag(
                                        resource_arn=arn,
                                        resource_native_id=cluster_name,
                                        key=k,
                                        value=v,
                                    )
                                )

                            specs = {
                                "version": version,
                                "endpoint": cluster.get("endpoint"),
                                "role_arn": cluster.get("roleArn"),
                            }

                            resources.append(
                                DiscoveredResource(
                                    native_id=cluster_name,
                                    arn=arn,
                                    service_name="AmazonEKS",
                                    resource_type="CLUSTER",
                                    region_code=reg,
                                    name=cluster_name,
                                    status=status,
                                    specs_json=specs,
                                )
                            )

                            # Discover Nodegroups for this cluster
                            ng_paginator = eks_client.get_paginator("list_nodegroups")
                            for ng_page in ng_paginator.paginate(clusterName=cluster_name):
                                for ng_name in ng_page.get("nodegroups", []):
                                    try:
                                        ng_res = eks_client.describe_nodegroup(
                                            clusterName=cluster_name,
                                            nodegroupName=ng_name,
                                        )
                                        ng = ng_res.get("nodegroup", {})
                                        ng_arn = ng.get("nodegroupArn") or f"arn:aws:eks:{reg}:{account_id}:nodegroup/{cluster_name}/{ng_name}"
                                        ng_status = ng.get("status", "ACTIVE").upper()

                                        for k, v in ng.get("tags", {}).items():
                                            tags.append(
                                                DiscoveredTag(
                                                    resource_arn=ng_arn,
                                                    resource_native_id=ng_name,
                                                    key=k,
                                                    value=v,
                                                )
                                            )

                                        ng_specs = {
                                            "cluster_name": cluster_name,
                                            "instance_types": ng.get("instanceTypes", []),
                                            "capacity_type": ng.get("capacityType", "ON_DEMAND"),
                                            "scaling_config": ng.get("scalingConfig", {}),
                                        }

                                        resources.append(
                                            DiscoveredResource(
                                                native_id=f"{cluster_name}/{ng_name}",
                                                arn=ng_arn,
                                                service_name="AmazonEKS",
                                                resource_type="NODEGROUP",
                                                region_code=reg,
                                                name=ng_name,
                                                status=ng_status,
                                                specs_json=ng_specs,
                                            )
                                        )
                                    except ClientError as e:
                                        logger.info("Describe nodegroup %s failed: %s", ng_name, e)

                        except ClientError as e:
                            logger.info("Describe cluster %s failed: %s", cluster_name, e)

            except ClientError as e:
                code = e.response.get("Error", {}).get("Code", "Unknown")
                msg = e.response.get("Error", {}).get("Message", str(e))
                logger.warning("EKS discovery failed in %s: %s - %s", reg, code, msg)
                failure_reason = f"EKS {reg}: {code} - {msg}"
            except Exception as e:
                logger.warning("EKS discovery error in %s: %s", reg, str(e))
                failure_reason = f"EKS {reg}: {str(e)}"

        return resources, tags, failure_reason
