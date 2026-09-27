"""
NEXORA ATLAS - Integration Schemas & Contracts
Sanitized Pydantic models for integration configuration, validation, and sync status.
Never serializes secrets, raw tokens, or External IDs back to clients.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.integrations.providers.base import AWSServicePermissions


class AWSConfigureRequest(BaseModel):
    """Payload to configure or update customer AWS IAM connection."""
    role_arn: str = Field(..., description="Customer AWS IAM Role ARN")
    external_id: Optional[str] = Field(None, description="Optional STS External ID")
    regions: List[str] = Field(default_factory=lambda: ["us-east-1"], description="Target AWS Regions")
    account_name: Optional[str] = Field(None, description="Friendly display name for account")


class AWSValidateRequest(BaseModel):
    """Payload to validate an AWS IAM connection on-demand."""
    role_arn: Optional[str] = None
    external_id: Optional[str] = None
    region: Optional[str] = "us-east-1"


class IntegrationItemResponse(BaseModel):
    """Sanitized integration entity representation."""
    id: str
    provider_type: str
    status: str
    auth_method: str
    role_arn_masked: Optional[str] = None
    regions: List[str] = Field(default_factory=list)
    account_name: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime


class AWSValidationResponse(BaseModel):
    """Connection validation result returned to UI."""
    is_valid: bool
    account_id: Optional[str] = None
    region: Optional[str] = None
    role_arn_masked: Optional[str] = None
    permissions: AWSServicePermissions
    error_message: Optional[str] = None


class SyncJobItemResponse(BaseModel):
    """Provenance and outcome record for a synchronization job."""
    id: str
    integration_id: str
    account_id: Optional[str] = None
    job_type: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    records_synced: int = 0
    error_message: Optional[str] = None


class IntegrationStatusResponse(BaseModel):
    """Comprehensive health, freshness, and capability status for an integration."""
    integration: IntegrationItemResponse
    permissions: AWSServicePermissions
    last_sync_job: Optional[SyncJobItemResponse] = None
    is_fresh: bool = False
    freshness_description: str = "Never synchronized"


class SyncTriggerResponse(BaseModel):
    """Response returned upon initiating a synchronization."""
    sync_job_id: str
    status: str
    account_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    resources_discovered: int = 0
    resources_created: int = 0
    resources_updated: int = 0
    cost_records_processed: int = 0
    cost_records_created: int = 0
    cost_records_updated: int = 0
    warnings: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
