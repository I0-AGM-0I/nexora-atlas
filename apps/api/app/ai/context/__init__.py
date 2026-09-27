"""
NEXORA ATLAS - AI Context & Sanitization Package (Phase 9)
Context builder, budget enforcement, prompt injection defense, and canonical hashing.
"""

from app.ai.context.builder import ContextBuilder
from app.ai.context.budget import enforce_budget, apply_context_budget
from app.ai.context.sanitizer import (
    sanitize_text,
    wrap_untrusted_metadata,
    sanitize_evidence_item,
    sanitize_user_question,
)
from app.ai.context.redaction import redact_secrets, redact_data_structure
from app.ai.context.canonicalizer import canonicalize_evidence_package, compute_evidence_hash
from app.ai.context.selectors import select_items_by_scope, select_items_by_epistemic_class

__all__ = [
    "ContextBuilder",
    "enforce_budget",
    "apply_context_budget",
    "sanitize_text",
    "wrap_untrusted_metadata",
    "sanitize_evidence_item",
    "sanitize_user_question",
    "redact_secrets",
    "redact_data_structure",
    "canonicalize_evidence_package",
    "compute_evidence_hash",
    "select_items_by_scope",
    "select_items_by_epistemic_class",
]
