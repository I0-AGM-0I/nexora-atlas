"""
NEXORA ATLAS - Context Budget Enforcement (Phase 9)
Enforces token and item budget constraints across evidence categories.
Never silently truncates; sets explicit limitation warnings if pruning occurs.
"""

from typing import List, Tuple
from app.ai.constants import (
    MAX_EVIDENCE_ITEMS,
    MAX_RESOURCES,
    MAX_RECOMMENDATIONS,
    MAX_SCENARIOS,
    MAX_TELEMETRY_SUMMARIES,
)
from app.ai.models import EvidencePackage, EvidenceItem
from app.ai.retrieval.ranking import rank_evidence_items


def apply_context_budget(
    items: List[EvidenceItem],
    max_items: int = MAX_EVIDENCE_ITEMS,
    target_entity_id: str = None,
) -> Tuple[List[EvidenceItem], int, int, bool]:
    """
    Deterministically ranks items and enforces budget cap without silent truncation.
    Returns: (included_items, included_count, excluded_count, is_context_limited)
    """
    total_count = len(items)
    if total_count <= max_items:
        return items, total_count, 0, False

    # Rank deterministically by epistemic class and relevance
    ranked = rank_evidence_items(items, target_entity_id=target_entity_id)
    included = ranked[:max_items]
    excluded_count = total_count - max_items
    return included, len(included), excluded_count, True


def enforce_budget(package: EvidencePackage) -> EvidencePackage:
    """
    Applies item limits to each category in the evidence package.
    If total items exceed MAX_EVIDENCE_ITEMS, trims lower-priority items
    and appends an explicit limitation disclosure.
    """
    pruned = False
    original_count = len(package.all_items())

    # Budget individual collections
    if len(package.recommendations) > MAX_RECOMMENDATIONS:
        package.recommendations = package.recommendations[:MAX_RECOMMENDATIONS]
        pruned = True

    if len(package.scenarios) > MAX_SCENARIOS:
        package.scenarios = package.scenarios[:MAX_SCENARIOS]
        pruned = True

    if len(package.telemetry) > MAX_TELEMETRY_SUMMARIES:
        package.telemetry = package.telemetry[:MAX_TELEMETRY_SUMMARIES]
        pruned = True

    # Total item cap
    all_count = len(package.all_items())
    if all_count > MAX_EVIDENCE_ITEMS:
        pruned = True
        overflow = all_count - MAX_EVIDENCE_ITEMS
        # Trim from telemetry first
        if len(package.telemetry) > overflow:
            package.telemetry = package.telemetry[:-overflow]
        else:
            overflow -= len(package.telemetry)
            package.telemetry = []
            if overflow > 0:
                if len(package.observations) > overflow:
                    package.observations = package.observations[:-overflow]
                else:
                    package.observations = []

    final_count = len(package.all_items())
    if pruned or final_count < original_count:
        package.is_context_limited = True
        excluded = original_count - final_count
        limit_note = (
            f"Context budget limit reached ({MAX_EVIDENCE_ITEMS} items maximum). "
            f"{excluded} lower-priority items were excluded from context."
        )
        if limit_note not in package.limitations:
            package.limitations.append(limit_note)

    package.evidence_count = len(package.all_items())
    return package
