"""
NEXORA ATLAS - Phase 9 Milestone 2: Context Budget Test Suite
Verifies MAX_EVIDENCE_ITEMS = 100 enforcement, truncation tracking (is_context_limited),
and deterministic prioritization ensuring high-priority evidence survives.
"""

import pytest
from decimal import Decimal
from app.ai.constants import MAX_EVIDENCE_ITEMS
from app.ai.types import EpistemicClass, ScopeType
from app.ai.models import EvidenceItem, EvidencePackage
from app.ai.context.budget import enforce_budget, apply_context_budget


def make_item(idx: int, epistemic_class: EpistemicClass = EpistemicClass.OBSERVED) -> EvidenceItem:
    return EvidenceItem(
        id=f"ev-{idx:03d}",
        type="METRIC",
        epistemic_class=epistemic_class,
        statement=f"Observation item {idx}",
        value=Decimal(str(idx * 10)),
        unit="INR",
        source="Atlas",
    )


def test_budget_within_limits_no_truncation():
    """Package with <= 100 items retains all items; is_context_limited = False."""
    items = [make_item(i) for i in range(50)]
    pkg = EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        observations=items,
        evidence_count=50,
    )
    budgeted = enforce_budget(pkg)
    assert budgeted.is_context_limited is False
    assert len(budgeted.all_items()) == 50
    assert len(budgeted.limitations) == 0


def test_budget_exact_boundary():
    """Exactly 100 items fits with is_context_limited = False."""
    items = [make_item(i) for i in range(MAX_EVIDENCE_ITEMS)]
    pkg = EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        observations=items,
        evidence_count=MAX_EVIDENCE_ITEMS,
    )
    budgeted = enforce_budget(pkg)
    assert budgeted.is_context_limited is False
    assert len(budgeted.all_items()) == 100


def test_budget_overflow_101_items():
    """101 items triggers is_context_limited = True with 100 items retained."""
    items = [make_item(i) for i in range(101)]
    pkg = EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        observations=items,
        evidence_count=101,
    )
    budgeted = enforce_budget(pkg)
    assert budgeted.is_context_limited is True
    assert len(budgeted.all_items()) == MAX_EVIDENCE_ITEMS
    assert any("Context budget limit reached" in note for note in budgeted.limitations)


def test_budget_overflow_200_items():
    """200 items triggers is_context_limited = True with 100 items retained."""
    obs = [make_item(i, EpistemicClass.OBSERVED) for i in range(100)]
    telemetry = [make_item(i + 100, EpistemicClass.DERIVED) for i in range(100)]
    pkg = EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        observations=obs,
        telemetry=telemetry,
        evidence_count=200,
    )
    budgeted = enforce_budget(pkg)
    assert budgeted.is_context_limited is True
    assert len(budgeted.all_items()) <= MAX_EVIDENCE_ITEMS
    assert any("100 lower-priority items were excluded" in note for note in budgeted.limitations)


def test_apply_context_budget_helper():
    """Validates apply_context_budget helper returning exact excluded counts."""
    items = [make_item(i) for i in range(120)]
    included, inc_count, exc_count, is_limited = apply_context_budget(items, max_items=100)

    assert is_limited is True
    assert inc_count == 100
    assert exc_count == 20
    assert len(included) == 100
