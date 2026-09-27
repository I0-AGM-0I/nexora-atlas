"""
NEXORA ATLAS - Tenant Scope Authorization (Phase 9)
Enforces multi-tenant authorization boundaries before query routing and retrieval.
Authorization determines what the user is allowed to access.
Classification only determines how to fulfill an authorized request.
"""

from typing import Optional, Dict, Any, List, Set
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.services.tenant import TenantContext
from app.ai.types import ScopeType
from app.models.resource import CloudResource
from app.models.account import CloudAccount
from app.models.optimization import Recommendation, OptimizationOpportunity
from app.models.scenario import Scenario


class AuthorizationScope(BaseModel):
    """
    Explicit authorization container establishing verified tenant boundary.
    All retrieval queries MUST be bounded by this scope.
    """
    organization_id: str
    allowed_account_ids: Set[str] = Field(default_factory=set)
    allowed_resource_ids: Set[str] = Field(default_factory=set)
    allowed_service_names: Set[str] = Field(default_factory=set)
    allowed_scenario_ids: Set[str] = Field(default_factory=set)
    allowed_recommendation_ids: Set[str] = Field(default_factory=set)

    @classmethod
    def from_tenant(cls, tenant: TenantContext) -> "AuthorizationScope":
        """Builds an AuthorizationScope from verified TenantContext."""
        return cls(
            organization_id=tenant.org_id,
            allowed_account_ids=set(tenant.account_ids),
        )

    def is_account_authorized(self, account_id: str) -> bool:
        return account_id in self.allowed_account_ids

    def is_resource_authorized(self, resource_id: str) -> bool:
        if not self.allowed_resource_ids:
            return True  # If empty, bounded by allowed_account_ids at query time
        return resource_id in self.allowed_resource_ids


class ScopeAuthorizationResult:
    """Carries validated target entity metadata and verified tenant ownership."""
    def __init__(
        self,
        scope_type: ScopeType,
        scope_id: Optional[str] = None,
        resolved_entity: Optional[Any] = None,
        account_ids: Optional[List[str]] = None,
        authorization_scope: Optional[AuthorizationScope] = None,
    ):
        self.scope_type = scope_type
        self.scope_id = scope_id
        self.resolved_entity = resolved_entity
        self.account_ids = account_ids or []
        self.authorization_scope = authorization_scope


async def authorize_scope(
    session: AsyncSession,
    tenant: TenantContext,
    scope_type: ScopeType,
    scope_id: Optional[str] = None,
) -> ScopeAuthorizationResult:
    """
    Validates tenant ownership of the requested scope before any evidence retrieval occurs.
    Raises HTTPException(404) on unauthorized or cross-tenant access attempts.
    """
    auth_scope = AuthorizationScope.from_tenant(tenant)

    if scope_type == ScopeType.DASHBOARD:
        return ScopeAuthorizationResult(
            scope_type=ScopeType.DASHBOARD,
            scope_id=None,
            account_ids=tenant.account_ids,
            authorization_scope=auth_scope,
        )

    if scope_type == ScopeType.ACCOUNT:
        if not scope_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account scope requires an account ID"
            )

        # Check by database UUID or AWS 12-digit account ID
        matched_account = None
        for acc in tenant.accounts:
            if acc.id == scope_id or acc.account_id == scope_id:
                matched_account = acc
                break

        if not matched_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account '{scope_id}' not found or access denied."
            )

        auth_scope.allowed_account_ids = {matched_account.id}
        return ScopeAuthorizationResult(
            scope_type=ScopeType.ACCOUNT,
            scope_id=matched_account.id,
            resolved_entity=matched_account,
            account_ids=[matched_account.id],
            authorization_scope=auth_scope,
        )

    if scope_type == ScopeType.RESOURCE:
        if not scope_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resource scope requires a resource ID"
            )

        # Look up resource strictly filtered by tenant account IDs
        query = (
            select(CloudResource)
            .where(
                (CloudResource.id == scope_id) | (CloudResource.native_id == scope_id),
                CloudResource.account_id.in_(tenant.account_ids)
            )
        )
        res = await session.execute(query)
        resource = res.scalars().first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource '{scope_id}' not found or access denied."
            )

        auth_scope.allowed_resource_ids = {resource.id, resource.native_id}
        return ScopeAuthorizationResult(
            scope_type=ScopeType.RESOURCE,
            scope_id=resource.id,
            resolved_entity=resource,
            account_ids=[resource.account_id],
            authorization_scope=auth_scope,
        )

    if scope_type == ScopeType.RECOMMENDATION:
        if not scope_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recommendation scope requires a recommendation ID"
            )

        query = (
            select(Recommendation)
            .join(OptimizationOpportunity)
            .where(
                Recommendation.id == scope_id,
                OptimizationOpportunity.account_id.in_(tenant.account_ids)
            )
        )
        res = await session.execute(query)
        rec = res.scalars().first()

        if not rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recommendation '{scope_id}' not found or access denied."
            )

        auth_scope.allowed_recommendation_ids = {rec.id}
        return ScopeAuthorizationResult(
            scope_type=ScopeType.RECOMMENDATION,
            scope_id=rec.id,
            resolved_entity=rec,
            account_ids=tenant.account_ids,
            authorization_scope=auth_scope,
        )

    if scope_type == ScopeType.SCENARIO:
        if not scope_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scenario scope requires a scenario ID"
            )

        query = (
            select(Scenario)
            .where(
                Scenario.id == scope_id,
                Scenario.org_id == tenant.org_id
            )
        )
        res = await session.execute(query)
        scen = res.scalars().first()

        if not scen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario '{scope_id}' not found or access denied."
            )

        auth_scope.allowed_scenario_ids = {scen.id}
        return ScopeAuthorizationResult(
            scope_type=ScopeType.SCENARIO,
            scope_id=scen.id,
            resolved_entity=scen,
            account_ids=tenant.account_ids,
            authorization_scope=auth_scope,
        )

    if scope_type == ScopeType.SERVICE:
        if scope_id:
            auth_scope.allowed_service_names = {scope_id.lower()}
        return ScopeAuthorizationResult(
            scope_type=ScopeType.SERVICE,
            scope_id=scope_id,
            account_ids=tenant.account_ids,
            authorization_scope=auth_scope,
        )

    return ScopeAuthorizationResult(
        scope_type=ScopeType.DASHBOARD,
        scope_id=None,
        account_ids=tenant.account_ids,
        authorization_scope=auth_scope,
    )
