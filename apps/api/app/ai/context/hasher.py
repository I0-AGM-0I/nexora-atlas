"""
NEXORA ATLAS - Canonical Evidence Hasher (Phase 9)
Re-exports from app.ai.context.canonicalizer for backward compatibility.
"""

from app.ai.context.canonicalizer import (
    canonicalize_evidence_package,
    compute_evidence_hash,
)

__all__ = [
    "canonicalize_evidence_package",
    "compute_evidence_hash",
]
