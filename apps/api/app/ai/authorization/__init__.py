"""
NEXORA ATLAS - Authorization Subsystem (Phase 9)
Pre-retrieval authorization boundary enforcing multi-tenant isolation.
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
