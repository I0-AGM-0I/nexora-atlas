"""
NEXORA ATLAS - Evidence Selectors (Phase 9)
Lightweight filtering and scope selector contracts for evidence package assembly.
"""

from typing import List, Optional
from app.ai.types import ScopeType, QuestionCategory, EpistemicClass
from app.ai.models import EvidenceItem, EvidencePackage


def select_items_by_scope(
    items: List[EvidenceItem],
    scope_type: ScopeType,
    scope_id: Optional[str] = None,
) -> List[EvidenceItem]:
    """Filters evidence items by scope type and optional target entity identifier."""
    if not scope_id:
        return items
    return [
        item for item in items
        if item.source_entity_id == scope_id or item.metadata.get("scope_id") == scope_id
    ]


def select_items_by_epistemic_class(
    package: EvidencePackage,
    epistemic_class: EpistemicClass,
) -> List[EvidenceItem]:
    """Filters evidence items within an evidence package by epistemic boundary."""
    return [item for item in package.all_items() if item.epistemic_class == epistemic_class]
