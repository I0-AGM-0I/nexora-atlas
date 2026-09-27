"""
NEXORA ATLAS - AWS CloudWatch Metric Registry & Catalog
Defines the authoritative catalog of supported CloudWatch metrics per resource type.
Pre-registered dimensions prevent noisy, expensive universal ListMetrics discovery.
"""

from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from app.integrations.providers.aws.telemetry.constants import (
    TELEMETRY_CATALOG_VERSION,
    DEFAULT_METRIC_PERIOD_SECONDS,
)


class MetricDefinition(BaseModel):
    """Authoritative definition for a supported CloudWatch metric."""
    provider: str = "AWS"
    namespace: str
    metric_name: str
    unit: str
    supported_resource_type: str  # INSTANCE, VOLUME, DATABASE, BUCKET, CLUSTER
    source_statistics: List[str]  # e.g. ["Average", "Maximum", "Sum"]
    default_period_seconds: int = DEFAULT_METRIC_PERIOD_SECONDS
    required_dimension_names: List[str]  # e.g. ["InstanceId"]
    interpretation: str
    is_activity_metric: bool = False  # True for I/O ops/bytes (not capacity utilization)
    version: str = TELEMETRY_CATALOG_VERSION


# Predefined Authoritative Catalog
_DEFINITIONS: List[MetricDefinition] = [
    # --- EC2 Virtual Instances ---
    MetricDefinition(
        namespace="AWS/EC2",
        metric_name="CPUUtilization",
        unit="Percent",
        supported_resource_type="INSTANCE",
        source_statistics=["Average", "Maximum"],
        required_dimension_names=["InstanceId"],
        interpretation="Percentage of allocated EC2 compute units currently in use on the instance.",
    ),
    MetricDefinition(
        namespace="AWS/EC2",
        metric_name="NetworkIn",
        unit="Bytes",
        supported_resource_type="INSTANCE",
        source_statistics=["Average", "Sum"],
        required_dimension_names=["InstanceId"],
        interpretation="Inbound network traffic bytes across all network interfaces of the instance.",
        is_activity_metric=True,
    ),
    MetricDefinition(
        namespace="AWS/EC2",
        metric_name="NetworkOut",
        unit="Bytes",
        supported_resource_type="INSTANCE",
        source_statistics=["Average", "Sum"],
        required_dimension_names=["InstanceId"],
        interpretation="Outbound network traffic bytes across all network interfaces of the instance.",
        is_activity_metric=True,
    ),
    MetricDefinition(
        namespace="AWS/EC2",
        metric_name="DiskReadBytes",
        unit="Bytes",
        supported_resource_type="INSTANCE",
        source_statistics=["Average", "Sum"],
        required_dimension_names=["InstanceId"],
        interpretation="Bytes read from all ephemeral and instance store disks attached to the instance.",
        is_activity_metric=True,
    ),
    MetricDefinition(
        namespace="AWS/EC2",
        metric_name="DiskWriteBytes",
        unit="Bytes",
        supported_resource_type="INSTANCE",
        source_statistics=["Average", "Sum"],
        required_dimension_names=["InstanceId"],
        interpretation="Bytes written to all ephemeral and instance store disks attached to the instance.",
        is_activity_metric=True,
    ),

    # --- RDS Relational Databases ---
    MetricDefinition(
        namespace="AWS/RDS",
        metric_name="CPUUtilization",
        unit="Percent",
        supported_resource_type="DATABASE",
        source_statistics=["Average", "Maximum"],
        required_dimension_names=["DBInstanceIdentifier"],
        interpretation="Percentage of CPU utilization on the database instance host.",
    ),
    MetricDefinition(
        namespace="AWS/RDS",
        metric_name="DatabaseConnections",
        unit="Count",
        supported_resource_type="DATABASE",
        source_statistics=["Average", "Maximum"],
        required_dimension_names=["DBInstanceIdentifier"],
        interpretation="Active client database connections currently open to the instance.",
        is_activity_metric=True,
    ),
    MetricDefinition(
        namespace="AWS/RDS",
        metric_name="FreeableMemory",
        unit="Bytes",
        supported_resource_type="DATABASE",
        source_statistics=["Average", "Minimum"],
        required_dimension_names=["DBInstanceIdentifier"],
        interpretation="Amount of available random access memory on the database instance host.",
    ),
    MetricDefinition(
        namespace="AWS/RDS",
        metric_name="ReadIOPS",
        unit="Count/Second",
        supported_resource_type="DATABASE",
        source_statistics=["Average"],
        required_dimension_names=["DBInstanceIdentifier"],
        interpretation="Average number of disk read I/O operations per second.",
        is_activity_metric=True,
    ),
    MetricDefinition(
        namespace="AWS/RDS",
        metric_name="WriteIOPS",
        unit="Count/Second",
        supported_resource_type="DATABASE",
        source_statistics=["Average"],
        required_dimension_names=["DBInstanceIdentifier"],
        interpretation="Average number of disk write I/O operations per second.",
        is_activity_metric=True,
    ),
    MetricDefinition(
        namespace="AWS/RDS",
        metric_name="FreeStorageSpace",
        unit="Bytes",
        supported_resource_type="DATABASE",
        source_statistics=["Average", "Minimum"],
        required_dimension_names=["DBInstanceIdentifier"],
        interpretation="Amount of available storage space on the database storage volume.",
    ),

    # --- EBS Block Storage Volumes ---
    # Note: EBS I/O metrics are explicitly classified as activity, NEVER capacity utilization.
    MetricDefinition(
        namespace="AWS/EBS",
        metric_name="VolumeReadOps",
        unit="Count",
        supported_resource_type="VOLUME",
        source_statistics=["Average", "Sum"],
        required_dimension_names=["VolumeId"],
        interpretation="Completed read I/O operations from the EBS volume during the period.",
        is_activity_metric=True,
    ),
    MetricDefinition(
        namespace="AWS/EBS",
        metric_name="VolumeWriteOps",
        unit="Count",
        supported_resource_type="VOLUME",
        source_statistics=["Average", "Sum"],
        required_dimension_names=["VolumeId"],
        interpretation="Completed write I/O operations to the EBS volume during the period.",
        is_activity_metric=True,
    ),
    MetricDefinition(
        namespace="AWS/EBS",
        metric_name="VolumeReadBytes",
        unit="Bytes",
        supported_resource_type="VOLUME",
        source_statistics=["Average", "Sum"],
        required_dimension_names=["VolumeId"],
        interpretation="Total bytes read from the EBS volume during the period.",
        is_activity_metric=True,
    ),
    MetricDefinition(
        namespace="AWS/EBS",
        metric_name="VolumeWriteBytes",
        unit="Bytes",
        supported_resource_type="VOLUME",
        source_statistics=["Average", "Sum"],
        required_dimension_names=["VolumeId"],
        interpretation="Total bytes written to the EBS volume during the period.",
        is_activity_metric=True,
    ),

    # --- S3 Object Storage Buckets ---
    MetricDefinition(
        namespace="AWS/S3",
        metric_name="BucketSizeBytes",
        unit="Bytes",
        supported_resource_type="BUCKET",
        source_statistics=["Average"],
        default_period_seconds=86400,  # S3 daily metric
        required_dimension_names=["BucketName", "StorageType"],
        interpretation="Total size of all objects stored in the bucket.",
    ),
    MetricDefinition(
        namespace="AWS/S3",
        metric_name="NumberOfObjects",
        unit="Count",
        supported_resource_type="BUCKET",
        source_statistics=["Average"],
        default_period_seconds=86400,  # S3 daily metric
        required_dimension_names=["BucketName", "StorageType"],
        interpretation="Total count of all objects stored in the bucket.",
        is_activity_metric=True,
    ),

    # --- EKS Kubernetes Clusters ---
    MetricDefinition(
        namespace="ContainerInsights",
        metric_name="cluster_failed_node_count",
        unit="Count",
        supported_resource_type="CLUSTER",
        source_statistics=["Average"],
        required_dimension_names=["ClusterName"],
        interpretation="Number of failed worker nodes in the EKS cluster.",
        is_activity_metric=True,
    ),
]


class MetricCatalog:
    """Provides queryable access to the authoritative metric registry."""
    _by_key: Dict[Tuple[str, str], MetricDefinition] = {
        (d.supported_resource_type, d.metric_name): d for d in _DEFINITIONS
    }
    _by_type: Dict[str, List[MetricDefinition]] = {}
    for d in _DEFINITIONS:
        _by_type.setdefault(d.supported_resource_type, []).append(d)

    @classmethod
    def get_definitions_for_resource(cls, resource_type: str) -> List[MetricDefinition]:
        """Returns all metric definitions registered for a given resource type."""
        return cls._by_type.get(resource_type.upper(), [])

    @classmethod
    def get_definition(cls, resource_type: str, metric_name: str) -> Optional[MetricDefinition]:
        """Looks up a specific metric definition by resource type and metric name."""
        return cls._by_key.get((resource_type.upper(), metric_name))

    @classmethod
    def get_dimension_name_for_resource(cls, resource_type: str) -> Optional[str]:
        """Returns the primary CloudWatch dimension name for the given resource type."""
        mapping = {
            "INSTANCE": "InstanceId",
            "VOLUME": "VolumeId",
            "DATABASE": "DBInstanceIdentifier",
            "BUCKET": "BucketName",
            "CLUSTER": "ClusterName",
        }
        return mapping.get(resource_type.upper())
