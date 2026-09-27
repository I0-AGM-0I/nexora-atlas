"""
NEXORA ATLAS - Phase 9 Milestone 1: AI Foundation & Contracts Test Suite
Validates the domain boundary, formal contracts, Pydantic models, epistemic invariants,
numeric tolerance contracts, recursive confidence prohibition, and boundary protocols.
"""

import pytest
import hashlib
from decimal import Decimal
from pydantic import ValidationError

from app.ai.constants import (
    AI_SYSTEM_VERSION,
    PROMPT_SYSTEM_VERSION,
    EXPLANATION_PROMPT_VERSION,
    CONTEXT_VERSION,
    NUMERICAL_TOLERANCE_RATIO,
    MAX_EVIDENCE_ITEMS,
    MAX_PERSISTED_EVIDENCE_BYTES,
)
from app.ai.types import (
    EpistemicClass,
    QuestionCategory,
    ScopeType,
    AIResponseStatus,
    ProviderErrorCode,
    DataFreshnessStatus,
    ValidationFailureReason,
    QUESTION_CATEGORY_ALLOWED_SCOPES,
)
from app.ai.models import (
    NumericClaim,
    EvidenceItem,
    EvidencePackage,
    DataFreshness,
    AIConclusion,
    AICitation,
    AIAnswer,
    AIResponse,
)
from app.ai.contracts import (
    validate_numeric_tolerance,
    reject_prohibited_fields,
    is_epistemic_upgrade_prohibited,
    ValidationGateResult,
    QueryClassifierContract,
    EvidenceRetrieverContract,
    AIProviderContract,
    ContextBuilderContract,
    ResponseValidatorContract,
    AIInteractionAuditContract,
)
from app.ai.explanations.response_parser import parse_provider_response, ParsedCandidateResponse
from app.ai.context.selectors import select_items_by_scope, select_items_by_epistemic_class


# ==============================================================================
# 1. DOMAIN ENUMS & CONSTANTS SPECIFICATION
# ==============================================================================

def test_epistemic_classes_specification():
    """All 6 foundational epistemic boundary classes must exist and be distinct."""
    expected_classes = {
        "OBSERVED",
        "DERIVED",
        "INFERRED",
        "ASSUMED",
        "PROJECTED",
        "NOT_AVAILABLE",
    }
    actual_classes = {c.value for c in EpistemicClass}
    assert actual_classes == expected_classes
    assert len(EpistemicClass) == 6


def test_question_categories_specification():
    """All 13 canonical natural-language question categories must exist."""
    expected_categories = {
        "SPEND_OVERVIEW",
        "SPEND_CHANGE",
        "COST_DRIVER",
        "ANOMALY",
        "OPTIMIZATION",
        "RESOURCE",
        "TELEMETRY",
        "SCENARIO",
        "FORECAST",
        "ACCOUNT",
        "SERVICE",
        "GENERAL_ATLAS",
        "UNSUPPORTED",
    }
    actual_categories = {q.value for q in QuestionCategory}
    assert actual_categories == expected_categories
    assert len(QuestionCategory) == 13


def test_scope_types_specification():
    """All 6 controlled scope boundaries must exist."""
    expected_scopes = {
        "DASHBOARD",
        "SERVICE",
        "ACCOUNT",
        "RESOURCE",
        "RECOMMENDATION",
        "SCENARIO",
    }
    actual_scopes = {s.value for s in ScopeType}
    assert actual_scopes == expected_scopes
    assert len(ScopeType) == 6


def test_question_category_allowed_scopes_mapping():
    """
    Correction 8: QuestionCategory <-> ScopeType must not be a rigid 1-to-1 mapping.
    Verifies that categories support multiple valid execution scopes.
    """
    assert QuestionCategory.COST_DRIVER in QUESTION_CATEGORY_ALLOWED_SCOPES
    allowed = QUESTION_CATEGORY_ALLOWED_SCOPES[QuestionCategory.COST_DRIVER]
    assert ScopeType.DASHBOARD in allowed
    assert ScopeType.SERVICE in allowed
    assert ScopeType.ACCOUNT in allowed
    assert ScopeType.RESOURCE in allowed

    # Every question category must have at least one valid scope
    for cat in QuestionCategory:
        assert cat in QUESTION_CATEGORY_ALLOWED_SCOPES
        assert len(QUESTION_CATEGORY_ALLOWED_SCOPES[cat]) >= 1


def test_system_constants_and_budgeting():
    """Validates centralized versioning, budgets, and tolerance constants."""
    assert AI_SYSTEM_VERSION == "0.1.0"
    assert PROMPT_SYSTEM_VERSION == "atlas-ai-v1"
    assert EXPLANATION_PROMPT_VERSION == "atlas-ai-explanation-v1"
    assert CONTEXT_VERSION == "atlas-ai-context-v1"
    assert NUMERICAL_TOLERANCE_RATIO == Decimal("0.01")
    assert MAX_EVIDENCE_ITEMS == 100
    assert MAX_PERSISTED_EVIDENCE_BYTES == 32768


# ==============================================================================
# 2. NUMERIC CLAIM & DECIMAL PRECISION CONTRACTS
# ==============================================================================

def test_numeric_claim_enforces_decimal_precision():
    """
    Correction 1: NumericClaim must use Decimal, never binary floating point.
    Coerces float/int/str into Decimal accurately.
    """
    # From float
    claim1 = NumericClaim(value=460000.0, unit="INR", evidence_id="spend-1")
    assert isinstance(claim1.value, Decimal)
    assert claim1.value == Decimal("460000.0")
    assert claim1.evidence_id == "spend-1"
    assert claim1.evidence_ids == ["spend-1"]

    # From Decimal
    claim2 = NumericClaim(
        value=Decimal("82500.50"),
        unit="INR",
        evidence_ids=["driver-eks-01"],
    )
    assert isinstance(claim2.value, Decimal)
    assert claim2.value == Decimal("82500.50")
    assert claim2.primary_evidence_id == "driver-eks-01"

    # From string
    claim3 = NumericClaim(value="14200.00", unit="INR", evidence_id="rec-01")
    assert isinstance(claim3.value, Decimal)
    assert claim3.value == Decimal("14200.00")


def test_numeric_tolerance_contract_with_decimal_precision():
    """
    Correction 2: Strict mathematical tolerance contract.
    absolute_error <= |A| * 0.01
    """
    auth = Decimal("100000.00")

    # Exact match passes
    assert validate_numeric_tolerance(Decimal("100000.00"), auth) is True

    # +0.5% deviation passes
    assert validate_numeric_tolerance(Decimal("100500.00"), auth) is True

    # Exact +1.0% boundary passes (101,000)
    assert validate_numeric_tolerance(Decimal("101000.00"), auth) is True

    # Exact -1.0% boundary passes (99,000)
    assert validate_numeric_tolerance(Decimal("99000.00"), auth) is True

    # +1.01% deviation fails (101,010)
    assert validate_numeric_tolerance(Decimal("101010.00"), auth) is False

    # -1.01% deviation fails (98,990)
    assert validate_numeric_tolerance(Decimal("98990.00"), auth) is False


def test_numeric_tolerance_zero_baseline_contract():
    """
    Correction 2: Explicit zero baseline handling.
    If authoritative value == 0, exact zero is required. Percentage tolerance is invalid.
    """
    auth_zero = Decimal("0.0")

    # Exact zero passes
    assert validate_numeric_tolerance(Decimal("0.0"), auth_zero) is True
    assert validate_numeric_tolerance(0, auth_zero) is True

    # Any non-zero claim fails against authoritative zero
    assert validate_numeric_tolerance(Decimal("1.0"), auth_zero) is False
    assert validate_numeric_tolerance(Decimal("0.01"), auth_zero) is False
    assert validate_numeric_tolerance(Decimal("-0.5"), auth_zero) is False


# ==============================================================================
# 3. RECURSIVE PROHIBITION OF AI-GENERATED CONFIDENCE
# ==============================================================================

def test_recursive_prohibition_of_confidence_in_raw_payload():
    """
    Correction 3 & 5: AI confidence prohibition must inspect entire nested payload.
    """
    # Root level confidence
    root_payload = {"confidence": 0.95, "answer": "text"}
    violations = reject_prohibited_fields(root_payload)
    assert len(violations) >= 1
    assert any("root.confidence" in v for v in violations)

    # Nested in conclusions -> metadata -> confidence
    deeply_nested_payload = {
        "conclusions": [
            {
                "statement": "Resource is idle.",
                "metadata": {
                    "analyzer_hints": {
                        "confidence": 0.88  # Prohibited deep inside
                    }
                }
            }
        ]
    }
    violations = reject_prohibited_fields(deeply_nested_payload)
    assert len(violations) >= 1
    assert any("confidence" in v for v in violations)

    # Clean payload passes with zero violations
    clean_payload = {
        "summary": "Valid summary",
        "conclusions": [
            {
                "statement": "Valid conclusion",
                "epistemic_class": "OBSERVED",
                "evidence_ids": ["ev-1"],
            }
        ]
    }
    assert len(reject_prohibited_fields(clean_payload)) == 0


def test_ai_models_reject_confidence_on_construction():
    """AIConclusion and AIAnswer models must reject payloads containing confidence."""
    with pytest.raises(ValidationError) as exc_info:
        AIConclusion(
            statement="Resource underutilized.",
            epistemic_class=EpistemicClass.INFERRED,
            confidence=0.92,  # type: ignore
        )
    assert "confidence" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info2:
        AIAnswer(
            summary="Summary",
            answer="Answer",
            confidence=0.99,  # type: ignore
        )
    assert "confidence" in str(exc_info2.value)


# ==============================================================================
# 4. EPISTEMIC BOUNDARY & UPGRADE PROHIBITION
# ==============================================================================

def test_epistemic_upgrade_prohibition_rules():
    """
    Correction 4: Epistemic boundary ordering rules.
    Prohibits AI from upgrading INFERRED, PROJECTED, ASSUMED, or NOT_AVAILABLE to OBSERVED facts.
    """
    # Prohibited upgrades
    assert is_epistemic_upgrade_prohibited(EpistemicClass.OBSERVED, EpistemicClass.INFERRED) is True
    assert is_epistemic_upgrade_prohibited(EpistemicClass.OBSERVED, EpistemicClass.PROJECTED) is True
    assert is_epistemic_upgrade_prohibited(EpistemicClass.OBSERVED, EpistemicClass.ASSUMED) is True
    assert is_epistemic_upgrade_prohibited(EpistemicClass.OBSERVED, EpistemicClass.NOT_AVAILABLE) is True

    # Prohibited presentation of projection as derived calculation
    assert is_epistemic_upgrade_prohibited(EpistemicClass.DERIVED, EpistemicClass.PROJECTED) is True
    assert is_epistemic_upgrade_prohibited(EpistemicClass.DERIVED, EpistemicClass.NOT_AVAILABLE) is True

    # Valid transitions (same level or valid framing)
    assert is_epistemic_upgrade_prohibited(EpistemicClass.OBSERVED, EpistemicClass.OBSERVED) is False
    assert is_epistemic_upgrade_prohibited(EpistemicClass.DERIVED, EpistemicClass.OBSERVED) is False
    assert is_epistemic_upgrade_prohibited(EpistemicClass.INFERRED, EpistemicClass.OBSERVED) is False
    assert is_epistemic_upgrade_prohibited(EpistemicClass.PROJECTED, EpistemicClass.PROJECTED) is False


# ==============================================================================
# 5. EVIDENCE ITEM IMMUTABILITY & PACKAGE DETERMINISM
# ==============================================================================

def test_evidence_item_is_frozen_immutable():
    """EvidenceItem must be immutable (frozen=True) to guarantee deterministic provenance."""
    item = EvidenceItem(
        id="spend-ec2-01",
        type="SPEND_TOTAL",
        epistemic_class=EpistemicClass.OBSERVED,
        statement="EC2 spend reached ₹210,000.",
        value=Decimal("210000.00"),
        unit="INR",
        source="AWS Cost Explorer",
    )

    with pytest.raises(ValidationError):
        item.statement = "Modified statement."  # type: ignore

    with pytest.raises(ValidationError):
        item.value = Decimal("999999.00")  # type: ignore


def test_evidence_package_canonical_hash_identity():
    """
    Correction 6: EvidencePackage must have a deterministic canonical SHA-256 identity.
    """
    item1 = EvidenceItem(
        id="spend-001",
        type="SPEND_TOTAL",
        epistemic_class=EpistemicClass.DERIVED,
        statement="Spend item",
        value=Decimal("50000.0"),
        unit="INR",
        source="Atlas",
    )
    pkg1 = EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        observations=[item1],
        evidence_count=1,
    )
    pkg2 = EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        observations=[item1],
        evidence_count=1,
    )

    hash1 = pkg1.compute_hash()
    hash2 = pkg2.compute_hash()
    assert hash1 == hash2
    assert len(hash1) == 64

    # Package methods
    assert pkg1.get_item("spend-001") == item1
    assert pkg1.get_numeric_item("spend-001") == item1
    assert pkg1.cited_evidence_ids() == ["spend-001"]
    assert pkg1.get_item("nonexistent") is None


# ==============================================================================
# 6. PROTOCOLS & BOUNDARY CONTRACTS
# ==============================================================================

def test_protocols_are_runtime_checkable():
    """Validates that lightweight Protocol boundary contracts are runtime checkable."""
    class DummyClassifier:
        def classify_question(self, question: str) -> QuestionCategory:
            return QuestionCategory.SPEND_OVERVIEW

    assert isinstance(DummyClassifier(), QueryClassifierContract)

    class DummyProvider:
        async def generate_explanation(
            self,
            evidence_package: EvidencePackage,
            user_question: str,
            session_context=None,
        ) -> AIResponse:
            return AIResponse(status=AIResponseStatus.COMPLETED)

    assert isinstance(DummyProvider(), AIProviderContract)


# ==============================================================================
# 7. PARSING != VALIDATION INVARIANT
# ==============================================================================

def test_response_parser_preserves_untrusted_candidate_contract():
    """
    Correction 10: Parsing != Validation.
    A successfully parsed response is an UNTRUSTED candidate, not authoritative evidence.
    """
    raw_markdown_json = """
    ```json
    {
      "summary": "High spend on RDS",
      "answer": "RDS spend surged 40%.",
      "conclusions": []
    }
    ```
    """
    candidate: ParsedCandidateResponse = parse_provider_response(raw_markdown_json)
    assert candidate.is_syntactically_valid is True
    assert candidate.parsed_json is not None
    assert candidate.parsed_json["summary"] == "High spend on RDS"

    # Malformed text produces safe failure without throwing unhandled exceptions
    malformed_candidate = parse_provider_response("This is plain text with no JSON.")
    assert malformed_candidate.is_syntactically_valid is False
    assert malformed_candidate.parsed_json is None
    assert malformed_candidate.parse_error is not None
