"""
NEXORA ATLAS - AI Response Validation Tests (Phase 9)
Tests mathematical claim verification, zero-hallucination tolerance,
epistemic class upgrade prevention, and prohibition of AI-generated confidence scores.
"""

import pytest
from app.ai.types import EpistemicClass, ScopeType
from app.ai.models import (
    EvidenceItem,
    EvidencePackage,
    NumericClaim,
    AIConclusion,
    AICitation,
    AIAnswer,
)
from app.ai.explanations.validator import AIResponseValidator


@pytest.fixture
def mock_evidence_package():
    """Builds a deterministic evidence package with known numbers and classifications."""
    items = [
        EvidenceItem(
            id="spend-total-001",
            type="SPEND_TOTAL",
            epistemic_class=EpistemicClass.DERIVED,
            statement="Total cloud spend is ₹460,000.",
            value=460000.0,
            unit="INR",
            source="Atlas Analytics Engine",
            confidence=1.0,
        ),
        EvidenceItem(
            id="driver-eks-001",
            type="COST_DRIVER",
            epistemic_class=EpistemicClass.DERIVED,
            statement="EKS contributed ₹82,000 to spend increase.",
            value=82000.0,
            unit="INR",
            source="Cost Explorer",
            confidence=1.0,
        ),
        EvidenceItem(
            id="rec-downsize-001",
            type="RECOMMENDATION",
            epistemic_class=EpistemicClass.INFERRED,
            statement="Rightsize instance to t3.medium with savings of ₹14,500.",
            value=14500.0,
            unit="INR",
            source="Atlas Optimizer",
            confidence=0.90,
        ),
        EvidenceItem(
            id="scen-graviton-001",
            type="SCENARIO",
            epistemic_class=EpistemicClass.PROJECTED,
            statement="Graviton migration project savings of ₹35,000.",
            value=35000.0,
            unit="INR",
            source="Atlas Scenario Planner",
            confidence=0.80,
        ),
        EvidenceItem(
            id="obs-zero-cost-001",
            type="COST_ITEM",
            epistemic_class=EpistemicClass.OBSERVED,
            statement="Unused resource incurred ₹0.00 cost.",
            value=0.0,
            unit="INR",
            source="Cost Explorer",
            confidence=1.0,
        ),
    ]

    return EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        observations=[items[1], items[4]],
        derived_metrics=[items[0]],
        inferences=[],
        recommendations=[items[2]],
        scenarios=[items[3]],
        telemetry=[],
        evidence_count=len(items),
    )


def test_validator_passes_valid_structured_claims(mock_evidence_package):
    """Verifies that an answer adhering to schema and numerical tolerances passes validation."""
    valid_payload = {
        "summary": "EKS drove ₹82,000 of the cost increase.",
        "answer": "Authoritative Cost Explorer records show EKS increased by ₹82,000.",
        "conclusions": [
            {
                "statement": "EKS contributed ₹82,000 to the spend increase.",
                "epistemic_class": "DERIVED",
                "evidence_ids": ["driver-eks-001"],
                "numeric_claims": [
                    {
                        "value": 82000.0,
                        "unit": "INR",
                        "evidence_id": "driver-eks-001",
                    }
                ],
            }
        ],
        "limitations": ["Data through finalized AWS bills."],
        "recommended_next_steps": ["Inspect EKS nodegroups."],
        "cited_entities": [],
        "epistemic_notes": ["Derived calculation."],
        "freshness_note": "Fresh data.",
    }

    result = AIResponseValidator.validate(valid_payload, mock_evidence_package)
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert result.answer is not None
    assert result.answer.conclusions[0].numeric_claims[0].value == 82000.0


def test_validator_accepts_values_within_one_percent_tolerance(mock_evidence_package):
    """Verifies that claims within the 1% numerical tolerance pass."""
    # 82,400 is +0.48% deviation from 82,000
    payload = {
        "summary": "Spend summary",
        "answer": "Detail",
        "conclusions": [
            {
                "statement": "EKS drove approximately ₹82,400.",
                "epistemic_class": "DERIVED",
                "evidence_ids": ["driver-eks-001"],
                "numeric_claims": [
                    {
                        "value": 82400.0,
                        "unit": "INR",
                        "evidence_id": "driver-eks-001",
                    }
                ],
            }
        ],
        "limitations": [],
        "recommended_next_steps": [],
        "cited_entities": [],
        "epistemic_notes": [],
    }

    result = AIResponseValidator.validate(payload, mock_evidence_package)
    assert result.is_valid is True


def test_validator_rejects_numerical_hallucination_exceeding_tolerance(mock_evidence_package):
    """
    Scenario J: Rejects numerical hallucinations.
    Claims ₹900,000 when evidence is ₹460,000.
    """
    hallucinated_payload = {
        "summary": "Total spend overview.",
        "answer": "Spend reached ₹900,000.",
        "conclusions": [
            {
                "statement": "Total cloud spend reached ₹900,000.",
                "epistemic_class": "DERIVED",
                "evidence_ids": ["spend-total-001"],
                "numeric_claims": [
                    {
                        "value": 900000.0,
                        "unit": "INR",
                        "evidence_id": "spend-total-001",
                    }
                ],
            }
        ],
        "limitations": [],
        "recommended_next_steps": [],
        "cited_entities": [],
        "epistemic_notes": [],
    }

    result = AIResponseValidator.validate(hallucinated_payload, mock_evidence_package)
    assert result.is_valid is False
    assert any("deviates" in err and "tolerance" in err for err in result.errors)


def test_validator_rejects_epistemic_upgrade_inferred_to_observed(mock_evidence_package):
    """Verifies that an INFERRED recommendation cannot be upgraded to OBSERVED."""
    invalid_upgrade_payload = {
        "summary": "Optimization finding.",
        "answer": "We observed this recommendation.",
        "conclusions": [
            {
                "statement": "We observed that downsizing saves ₹14,500.",
                "epistemic_class": "OBSERVED",  # INVALID: rec-downsize-001 is INFERRED
                "evidence_ids": ["rec-downsize-001"],
                "numeric_claims": [
                    {
                        "value": 14500.0,
                        "unit": "INR",
                        "evidence_id": "rec-downsize-001",
                    }
                ],
            }
        ],
        "limitations": [],
        "recommended_next_steps": [],
        "cited_entities": [],
        "epistemic_notes": [],
    }

    result = AIResponseValidator.validate(invalid_upgrade_payload, mock_evidence_package)
    assert result.is_valid is False
    assert any("upgraded epistemic status to OBSERVED" in err for err in result.errors)


def test_validator_rejects_epistemic_upgrade_projected_to_observed_or_derived(mock_evidence_package):
    """Verifies that PROJECTED scenarios cannot be presented as DERIVED or OBSERVED."""
    invalid_projected_payload = {
        "summary": "Graviton scenario.",
        "answer": "We derived actual savings.",
        "conclusions": [
            {
                "statement": "Graviton produced ₹35,000 in savings.",
                "epistemic_class": "DERIVED",  # INVALID: scen-graviton-001 is PROJECTED
                "evidence_ids": ["scen-graviton-001"],
                "numeric_claims": [
                    {
                        "value": 35000.0,
                        "unit": "INR",
                        "evidence_id": "scen-graviton-001",
                    }
                ],
            }
        ],
        "limitations": [],
        "recommended_next_steps": [],
        "cited_entities": [],
        "epistemic_notes": [],
    }

    result = AIResponseValidator.validate(invalid_projected_payload, mock_evidence_package)
    assert result.is_valid is False
    assert any("invalidly presented PROJECTED evidence" in err for err in result.errors)


def test_validator_prohibits_ai_generated_confidence_scores(mock_evidence_package):
    """
    Correction 3: AI-generated confidence scores are strictly prohibited.
    Verifies that any output attempting to generate confidence is rejected.
    """
    prohibited_root_confidence = {
        "summary": "Summary",
        "answer": "Detail",
        "confidence": 0.95,  # PROHIBITED!
        "conclusions": [],
        "limitations": [],
        "recommended_next_steps": [],
        "cited_entities": [],
        "epistemic_notes": [],
    }

    result = AIResponseValidator.validate(prohibited_root_confidence, mock_evidence_package)
    assert result.is_valid is False
    assert any("AI-generated confidence score detected" in err for err in result.errors)


def test_validator_rejects_nonexistent_evidence_id(mock_evidence_package):
    """Verifies that citing a fabricated evidence ID is rejected."""
    hallucinated_id_payload = {
        "summary": "Summary",
        "answer": "Detail",
        "conclusions": [
            {
                "statement": "Fabricated finding.",
                "epistemic_class": "DERIVED",
                "evidence_ids": ["fabricated-id-999"],  # Nonexistent
                "numeric_claims": [],
            }
        ],
        "limitations": [],
        "recommended_next_steps": [],
        "cited_entities": [],
        "epistemic_notes": [],
    }

    result = AIResponseValidator.validate(hallucinated_id_payload, mock_evidence_package)
    assert result.is_valid is False
    assert any("nonexistent evidence_id" in err for err in result.errors)
