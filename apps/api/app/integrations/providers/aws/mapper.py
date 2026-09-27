"""
NEXORA ATLAS - AWS Normalization & Model Mapper
Maps AWS-discovered DTOs to canonical Atlas persistence models.
Enforces composite resource identity (ARN when available; else provider + account + service + native_id).
"""

from typing import Dict, Any, Optional
from app.models.account import CloudAccount, CloudRegion
from app.models.resource import CloudResource, Tag
from app.models.cost import CostRecord
from app.integrations.providers.base import (
    DiscoveredAccount,
    DiscoveredRegion,
    DiscoveredResource,
    DiscoveredTag,
    DiscoveredCostRecord,
)


class AWSModelMapper:
    """Normalizes provider DTOs into canonical Atlas models."""

    @staticmethod
    def get_resource_composite_key(
        provider_type: str,
        account_id: str,
        service_name: str,
        native_id: str,
        arn: Optional[str] = None,
    ) -> str:
        """
        Builds deterministic composite resource identity.
        Uses ARN if available; otherwise falls back to provider + account + service + native_id.
        Prevents cross-service collision on native_id alone.
        """
        if arn:
            return f"{provider_type}::{account_id}::{arn}"
        return f"{provider_type}::{account_id}::{service_name}::{native_id}"

    @classmethod
    def to_cloud_account(
        cls,
        dto: DiscoveredAccount,
        org_id: str,
    ) -> CloudAccount:
        return CloudAccount(
            org_id=org_id,
            provider_type=dto.provider_type,
            account_id=dto.account_id,
            name=dto.name,
            status="ACTIVE",
        )

    @classmethod
    def to_cloud_region(
        cls,
        dto: DiscoveredRegion,
    ) -> CloudRegion:
        return CloudRegion(
            provider_type=dto.provider_type,
            region_code=dto.region_code,
            display_name=dto.display_name,
        )

    @classmethod
    def to_cloud_resource(
        cls,
        dto: DiscoveredResource,
        account_db_id: str,
        region_db_id: Optional[str] = None,
    ) -> CloudResource:
        return CloudResource(
            account_id=account_db_id,
            region_id=region_db_id,
            service_name=dto.service_name,
            resource_type=dto.resource_type,
            resource_arn=dto.arn,
            native_id=dto.native_id,
            name=dto.name or dto.native_id,
            status=dto.status,
            specs_json=dto.specs_json,
        )

    @classmethod
    def to_tag(
        cls,
        dto: DiscoveredTag,
        resource_db_id: str,
    ) -> Tag:
        return Tag(
            resource_id=resource_db_id,
            key=dto.key,
            value=dto.value,
        )

    @classmethod
    def to_cost_record(
        cls,
        dto: DiscoveredCostRecord,
        account_db_id: str,
        resource_db_id: Optional[str] = None,
    ) -> CostRecord:
        return CostRecord(
            account_id=account_db_id,
            resource_id=resource_db_id,
            service_name=dto.service_name,
            usage_date=dto.usage_date,
            unblended_cost=dto.unblended_cost,
            amortized_cost=dto.amortized_cost,
            usage_quantity=dto.usage_quantity or 0,
            usage_unit=dto.usage_unit or "Hrs",
            currency=dto.currency,
        )
