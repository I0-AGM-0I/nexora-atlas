"""
NEXORA ATLAS - Canonical Context Serializer (Phase 9)
Produces deterministic, sorted, stable JSON representations of EvidencePackages.

CRITICAL INVARIANTS:
  same evidence + same ordering + same metadata = same canonical JSON = same SHA-256.
  Financial Decimals serialize stably without float rounding artifacts.
  Stable list ordering and dictionary key sorting across all platforms.
"""

import json
import hashlib
from decimal import Decimal
from typing import Any, Union
from app.ai.models import EvidencePackage, EvidenceItem


def _canonical_json_default(obj: Any) -> Any:
    """Standardizes types for deterministic JSON serialization."""
    if isinstance(obj, Decimal):
        # Format decimal with exact string representation
        return str(obj)
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if hasattr(obj, "dict"):
        return obj.dict()
    return str(obj)


def canonicalize_evidence_package(package: EvidencePackage) -> str:
    """
    Serializes an EvidencePackage into a canonical, deterministically sorted JSON string.
    Ensures identical evidence packages produce identical SHA-256 hashes across platforms.
    """
    data = package.model_dump(mode="json")
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        default=_canonical_json_default,
        ensure_ascii=True,
    )


def compute_evidence_hash(package: EvidencePackage) -> str:
    """Computes a SHA-256 digest over the canonicalized evidence package."""
    canonical_json = canonicalize_evidence_package(package)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
