"""
NEXORA ATLAS - Evidence Ranking (Phase 9)
Deterministically orders evidence items by epistemic class and categorical relevance.

CRITICAL INVARIANT:
  No hidden numerical "evidence quality scores".
  Orders strictly by categorical hierarchy:
    1. Directly relevant OBSERVED
    2. Directly relevant DERIVED
    3. Directly relevant INFERRED
    4. Relevant ASSUMED
    5. Relevant PROJECTED
    6. NOT_AVAILABLE diagnostics
"""

from typing import List, Optional
from app.ai.types import EpistemicClass
from app.ai.models import EvidenceItem

EPISTEMIC_RANK_PRIORITY = {
    EpistemicClass.OBSERVED: 1,
    EpistemicClass.DERIVED: 2,
    EpistemicClass.INFERRED: 3,
    EpistemicClass.ASSUMED: 4,
    EpistemicClass.PROJECTED: 5,
    EpistemicClass.NOT_AVAILABLE: 6,
}


def rank_evidence_items(
    items: List[EvidenceItem],
    target_entity_id: Optional[str] = None,
) -> List[EvidenceItem]:
    """
    Deterministically sorts evidence items using strict categorical hierarchy.
    Preserves relative order within matching categories.
    """
    def _rank_key(item: EvidenceItem):
        # 1. Epistemic class tier (1 to 6)
        tier = EPISTEMIC_RANK_PRIORITY.get(item.epistemic_class, 99)

        # 2. Entity relevance bonus (0 for matching target entity, 1 otherwise)
        entity_rel = 0 if target_entity_id and item.source_entity_id == target_entity_id else 1

        # 3. Source specificity (items with numerical values prioritized slightly over purely descriptive text)
        has_val = 0 if item.value is not None else 1

        # 4. Deterministic stable tie-breaker using item ID
        return (tier, entity_rel, has_val, item.id)

    return sorted(items, key=_rank_key)
