"""
NEXORA ATLAS - Provider Abstraction & Data Transfer Objects
Establishes canonical provider-neutral schemas and interfaces.
No cloud-specific SDK types are permitted to leak beyond this layer.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import date
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CostAttributionLevel(str, Enum):
    """Granularity level of billing data attribution."""
    ACCOUNT = "ACCOUNT"
    SERVICE = "SERVICE"
    RESOURCE = "RESOURCE"
    UNATTRIBUTED = "UNATTRIBUTED"


class PermissionStatus(str, Enum):
    """Read-only capability access status."""
    AVAILABLE = "AVAILABLE"
    DENIED = "DENIED"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class DiscoveredAccount(BaseModel):
    """Account identity discovered from cloud provider."""
    account_id: str
    name: str
    provider_type: str = "AWS"


class DiscoveredRegion(BaseModel):
    """Geographic region discovered from cloud provider."""
    region_code: str
    display_name: str
    provider_type: str = "AWS"


class DiscoveredResource(BaseModel):
    """Infrastructure resource discovered from cloud provider."""
    native_id: str
    arn: Optional[str] = None
    service_name: str
    resource_type: str
    region_code: Optional[str] = None
    name: Optional[str] = None
    status: str = "ACTIVE"
    specs_json: Dict[str, Any] = Field(default_factory=dict)


class DiscoveredTag(BaseModel):
    """Tag metadata discovered on cloud resources."""
    resource_arn: Optional[str] = None
    resource_native_id: str
    key: str
    value: str


class DiscoveredCostRecord(BaseModel):
    """Financial billing record retrieved from cloud provider."""
    usage_date: date
    service_name: str
    unblended_cost: Decimal
    amortized_cost: Decimal
    usage_quantity: Optional[Decimal] = None
    usage_unit: Optional[str] = None
    usage_type: Optional[str] = None
    operation: Optional[str] = None
    currency: str = "USD"
    resource_native_id: Optional[str] = None
    attribution_level: CostAttributionLevel = CostAttributionLevel.SERVICE
    source_record_key: str


class AWSServicePermissions(BaseModel):
    """Granular permission status matrix across AWS service capabilities."""
    cost_aggregated: PermissionStatus = PermissionStatus.NOT_CONFIGURED
    cost_resource_level: PermissionStatus = PermissionStatus.NOT_CONFIGURED
    ec2_inventory: PermissionStatus = PermissionStatus.NOT_CONFIGURED
    ebs_inventory: PermissionStatus = PermissionStatus.NOT_CONFIGURED
    rds_inventory: PermissionStatus = PermissionStatus.NOT_CONFIGURED
    s3_inventory: PermissionStatus = PermissionStatus.NOT_CONFIGURED
    eks_inventory: PermissionStatus = PermissionStatus.NOT_CONFIGURED
    cloudwatch_telemetry: PermissionStatus = PermissionStatus.NOT_CONFIGURED
    ec2_cpu_telemetry: PermissionStatus = PermissionStatus.NOT_CONFIGURED
    rds_cpu_telemetry: PermissionStatus = PermissionStatus.NOT_CONFIGURED
    ebs_io_telemetry: PermissionStatus = PermissionStatus.NOT_CONFIGURED
    s3_telemetry: PermissionStatus = PermissionStatus.NOT_CONFIGURED
    eks_telemetry: PermissionStatus = PermissionStatus.NOT_CONFIGURED


class ConnectionValidationResult(BaseModel):
    """Sanitized result of an integration connection validation probe."""
    is_valid: bool
    account_id: Optional[str] = None
    region: Optional[str] = None
    role_arn_masked: Optional[str] = None
    permissions: AWSServicePermissions = Field(default_factory=AWSServicePermissions)
    error_message: Optional[str] = None


class BaseCloudProvider(ABC):
    """Abstract read-only cloud provider interface."""

    @abstractmethod
    async def validate_connection(self) -> ConnectionValidationResult:
        """Validates credentials and read-only service permissions."""
        pass

    @abstractmethod
    async def discover_account(self) -> DiscoveredAccount:
        """Discovers account identity."""
        pass

    @abstractmethod
    async def discover_regions(self) -> List[DiscoveredRegion]:
        """Discovers active cloud regions."""
        pass

    @abstractmethod
    async def discover_resources(
        self,
        regions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Discovers inventory resources and tags across supported services.
        Returns dict with:
        - resources: List[DiscoveredResource]
        - tags: List[DiscoveredTag]
        - partial_failures: Dict[str, str] (service_name -> error_msg)
        """
        pass

    @abstractmethod
    async def discover_costs(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        Retrieves billing cost records for the specified period.
        Returns dict with:
        - records: List[DiscoveredCostRecord]
        - resource_level_available: bool
        - warnings: List[str]
        """
        pass
