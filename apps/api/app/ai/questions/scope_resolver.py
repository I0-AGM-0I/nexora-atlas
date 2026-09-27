"""
NEXORA ATLAS - Scope Resolver (Phase 9)
Resolves requested scope from natural language inquiry and intersects it with
pre-authorized tenant boundaries.

CRITICAL INVARIANT:
  Requested Scope ∩ Authorized Scope = Effective Retrieval Scope.
  If the intersection is empty, the result is NOT_AVAILABLE / NOT_AUTHORIZED;
  never a cross-tenant leakage.
"""

from typing import Optional, Tuple
from pydantic import BaseModel
from app.ai.types import ScopeType, QuestionCategory
from app.ai.authorization.scope import AuthorizationScope


class ResolvedScope(BaseModel):
    """Result of intersecting requested entity scope with authorized tenant scope."""
    scope_type: ScopeType
    scope_id: Optional[str] = None
    is_authorized: bool = True
    denial_reason: Optional[str] = None


class ScopeResolver:
    """
    Deterministically reconciles requested inquiry scope against an AuthorizationScope.
    """

    @classmethod
    def resolve_scope(
        cls,
        requested_scope_type: ScopeType,
        requested_scope_id: Optional[str],
        auth_scope: AuthorizationScope,
        category: Optional[QuestionCategory] = None,
    ) -> ResolvedScope:
        """
        Intersects requested scope against authorized scope.
        """
        # 1. DASHBOARD: always valid within tenant organization
        if requested_scope_type == ScopeType.DASHBOARD:
            return ResolvedScope(
                scope_type=ScopeType.DASHBOARD,
                scope_id=None,
                is_authorized=True,
            )

        # 2. ACCOUNT: must belong to authorized account IDs
        if requested_scope_type == ScopeType.ACCOUNT:
            if not requested_scope_id:
                return ResolvedScope(
                    scope_type=ScopeType.ACCOUNT,
                    scope_id=None,
                    is_authorized=False,
                    denial_reason="Account scope requires an account ID",
                )
            if not auth_scope.is_account_authorized(requested_scope_id):
                return ResolvedScope(
                    scope_type=ScopeType.ACCOUNT,
                    scope_id=requested_scope_id,
                    is_authorized=False,
                    denial_reason=f"Account '{requested_scope_id}' is not in authorized tenant scope",
                )
            return ResolvedScope(
                scope_type=ScopeType.ACCOUNT,
                scope_id=requested_scope_id,
                is_authorized=True,
            )

        # 3. RESOURCE: must belong to authorized resources or tenant accounts
        if requested_scope_type == ScopeType.RESOURCE:
            if not requested_scope_id:
                return ResolvedScope(
                    scope_type=ScopeType.RESOURCE,
                    scope_id=None,
                    is_authorized=False,
                    denial_reason="Resource scope requires a resource ID",
                )
            if not auth_scope.is_resource_authorized(requested_scope_id):
                return ResolvedScope(
                    scope_type=ScopeType.RESOURCE,
                    scope_id=requested_scope_id,
                    is_authorized=False,
                    denial_reason=f"Resource '{requested_scope_id}' is not in authorized tenant scope",
                )
            return ResolvedScope(
                scope_type=ScopeType.RESOURCE,
                scope_id=requested_scope_id,
                is_authorized=True,
            )

        # 4. RECOMMENDATION
        if requested_scope_type == ScopeType.RECOMMENDATION:
            if not requested_scope_id:
                return ResolvedScope(
                    scope_type=ScopeType.RECOMMENDATION,
                    scope_id=None,
                    is_authorized=False,
                    denial_reason="Recommendation scope requires a recommendation ID",
                )
            if auth_scope.allowed_recommendation_ids and requested_scope_id not in auth_scope.allowed_recommendation_ids:
                return ResolvedScope(
                    scope_type=ScopeType.RECOMMENDATION,
                    scope_id=requested_scope_id,
                    is_authorized=False,
                    denial_reason=f"Recommendation '{requested_scope_id}' is not in authorized tenant scope",
                )
            return ResolvedScope(
                scope_type=ScopeType.RECOMMENDATION,
                scope_id=requested_scope_id,
                is_authorized=True,
            )

        # 5. SCENARIO
        if requested_scope_type == ScopeType.SCENARIO:
            if not requested_scope_id:
                return ResolvedScope(
                    scope_type=ScopeType.SCENARIO,
                    scope_id=None,
                    is_authorized=False,
                    denial_reason="Scenario scope requires a scenario ID",
                )
            if auth_scope.allowed_scenario_ids and requested_scope_id not in auth_scope.allowed_scenario_ids:
                return ResolvedScope(
                    scope_type=ScopeType.SCENARIO,
                    scope_id=requested_scope_id,
                    is_authorized=False,
                    denial_reason=f"Scenario '{requested_scope_id}' is not in authorized tenant scope",
                )
            return ResolvedScope(
                scope_type=ScopeType.SCENARIO,
                scope_id=requested_scope_id,
                is_authorized=True,
            )

        # 6. SERVICE
        if requested_scope_type == ScopeType.SERVICE:
            return ResolvedScope(
                scope_type=ScopeType.SERVICE,
                scope_id=requested_scope_id,
                is_authorized=True,
            )

        return ResolvedScope(
            scope_type=ScopeType.DASHBOARD,
            scope_id=None,
            is_authorized=True,
        )
