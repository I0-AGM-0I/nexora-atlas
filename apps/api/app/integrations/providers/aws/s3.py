"""
NEXORA ATLAS - AWS S3 Read-Only Adapter
Discovers bucket inventory, region via HeadBucket, versioning, and tags.
Strictly paginated via SDK paginator. Zero object listing or inspection.
"""

import logging
from typing import List, Tuple, Optional
from botocore.exceptions import ClientError

from app.integrations.providers.base import (
    DiscoveredResource,
    DiscoveredTag,
)
from app.integrations.providers.aws.client import AWSClientFactory

logger = logging.getLogger("atlas.aws.s3")


class AWSS3Adapter:
    """Read-only adapter for Amazon S3 metadata."""

    def __init__(self, client_factory: AWSClientFactory):
        self.client_factory = client_factory

    def describe_buckets(
        self,
        account_id: str,
    ) -> Tuple[List[DiscoveredResource], List[DiscoveredTag], Optional[str]]:
        """
        Discovers S3 buckets with pagination, resolving bucket region via HeadBucket.
        Returns: (resources, tags, failure_reason)
        """
        s3_client = self.client_factory.get_client("s3")
        resources: List[DiscoveredResource] = []
        tags: List[DiscoveredTag] = []
        failure_reason: Optional[str] = None

        try:
            # Correction 4: Paginated ListBuckets
            paginator = s3_client.get_paginator("list_buckets")
            for page in paginator.paginate():
                for bucket in page.get("Buckets", []):
                    b_name = bucket.get("Name")
                    if not b_name:
                        continue

                    arn = f"arn:aws:s3:::{b_name}"
                    creation_date = (
                        bucket.get("CreationDate").isoformat()
                        if bucket.get("CreationDate")
                        else None
                    )

                    # Correction 3: Resolve bucket region via HeadBucket
                    bucket_region = "us-east-1"
                    try:
                        head_res = s3_client.head_bucket(Bucket=b_name)
                        headers = head_res.get("ResponseMetadata", {}).get("HTTPHeaders", {})
                        bucket_region = (
                            headers.get("x-amz-bucket-region")
                            or s3_client.meta.region_name
                            or "us-east-1"
                        )
                    except ClientError as e:
                        headers = e.response.get("ResponseMetadata", {}).get("HTTPHeaders", {})
                        if "x-amz-bucket-region" in headers:
                            bucket_region = headers["x-amz-bucket-region"]
                        else:
                            logger.info("HeadBucket access denied or region defaulted for %s", b_name)

                    # Inspect versioning status (gracefully handle AccessDenied)
                    versioning_status = "Disabled"
                    try:
                        v_res = s3_client.get_bucket_versioning(Bucket=b_name)
                        versioning_status = v_res.get("Status", "Disabled")
                    except ClientError:
                        pass

                    # Inspect bucket tags (gracefully handle NoSuchTagSet or AccessDenied)
                    try:
                        t_res = s3_client.get_bucket_tagging(Bucket=b_name)
                        for t in t_res.get("TagSet", []):
                            k, v = t.get("Key"), t.get("Value")
                            if k and v is not None:
                                tags.append(
                                    DiscoveredTag(
                                        resource_arn=arn,
                                        resource_native_id=b_name,
                                        key=k,
                                        value=v,
                                    )
                                )
                    except ClientError:
                        pass

                    specs = {
                        "creation_date": creation_date,
                        "versioning": versioning_status,
                        "lifecycle_rules_configured": None,  # Can be expanded safely later
                    }

                    resources.append(
                        DiscoveredResource(
                            native_id=b_name,
                            arn=arn,
                            service_name="AmazonS3",
                            resource_type="BUCKET",
                            region_code=bucket_region,
                            name=b_name,
                            status="ACTIVE",
                            specs_json=specs,
                        )
                    )

        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "Unknown")
            msg = e.response.get("Error", {}).get("Message", str(e))
            logger.warning("S3 discovery failed: %s - %s", code, msg)
            failure_reason = f"S3: {code} - {msg}"
        except Exception as e:
            logger.warning("S3 discovery error: %s", str(e))
            failure_reason = f"S3: {str(e)}"

        return resources, tags, failure_reason
