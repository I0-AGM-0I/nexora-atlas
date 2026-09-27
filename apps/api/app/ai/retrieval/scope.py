"""
NEXORA ATLAS - Tenant Scope Authorization (Phase 9)
Re-exports from app.ai.authorization.scope for backward compatibility.
"""

from app.ai.authorization.scope import (
    AuthorizationScope,
    ScopeAuthorizationResult,
    authorize_scope,
)

__all__ = [
    "AuthorizationScope",
    "ScopeAuthorizationResult",
    "authorize_scope",
]
