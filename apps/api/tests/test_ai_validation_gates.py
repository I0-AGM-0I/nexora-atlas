"""
NEXORA ATLAS - AI Response Validation Gates Test Suite (Phase 9 Milestone 4)
Exhaustively tests all 8 validation gates individually:
1. Schema Validation
2. Evidence-ID Resolution
3. Numeric Claim Tolerance & Semantic Matching
4. Epistemic Integrity & Upgrade Prohibition
5. Citation Integrity & Completeness
6. Recursive Confidence Score Prohibition
7. Prompt Injection Defense & Secret Leak Prevention
8. Limitation Preservation & Freshness Qualification
"""

import pytest
from decimal import Decimal
from typing import Dict, Any

from app.ai.types import EpistemicClass, ScopeType, DataFreshnessStatus
from app.ai.models import (
    EvidenceItem,
    EvidencePackage,
    DataFreshness,
)
from app.ai.providers.models import (
    AICandidateAnswer,
    AICandidateConclusion,
    AICandidateNumericClaim,
    AICandidateCitation,
)
from app.ai.validation.result import ValidationStatus
from app.ai.validation.schema import SchemaValidator
from app.ai.validation.evidence import EvidenceValidator
from app.ai.validation.numeric import NumericValidator
from app.ai.validation.epistemic import EpistemicValidator
from app.ai.validation.citations import CitationValidator
from app.ai.validation.security import SecurityValidator
from app.ai.validation.limitations import LimitationsValidator
from app.ai.validation.validator import ResponseValidator


@pytest.fixture
def sample_evidence_package():
    """Provides authoritative evidence items covering all categories."""
    obs1 = EvidenceItem(
        id="ev-eks-cost",
        type="COST_DRIVER",
        epistemic_class=EpistemicClass.OBSERVED,
        statement="EKS cluster spend is ₹82,000.00.",
        value=Decimal("82000.00"),
        unit="INR",
        source="Cost Explorer",
    )
    obs2 = EvidenceItem(
        id="ev-zero-cost",
        type="COST_ITEM",
        epistemic_class=EpistemicClass.OBSERVED,
        statement="Idle backup storage is ₹0.00.",
        value=Decimal("0.00"),
        unit="INR",
        source="Cost Explorer",
    )
    rec1 = EvidenceItem(
        id="ev-rec-downsize",
        type="RECOMMENDATION",
        epistemic_class=EpistemicClass.INFERRED,
        statement="Downsize compute node for ₹14,500.00 savings.",
        value=Decimal("14500.00"),
        unit="INR",
        source="Atlas Optimizer",
    )
    scen1 = EvidenceItem(
        id="ev-scen-graviton",
        type="SCENARIO",
        epistemic_class=EpistemicClass.PROJECTED,
        statement="Modernization simulation projects ₹35,000.00 monthly savings.",
        value=Decimal("35000.00"),
        unit="INR",
        source="Scenario Planner",
    )
    telem_missing = EvidenceItem(
        id="ev-telem-db",
        type="TELEMETRY",
        epistemic_class=EpistemicClass.NOT_AVAILABLE,
        statement="CloudWatch telemetry not available for database cluster.",
        value=None,
        unit=None,
        source="CloudWatch",
    )

    return EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        observations=[obs1, obs2],
        recommendations=[rec1],
        scenarios=[scen1],
        telemetry=[telem_missing],
        evidence_count=5,
    )


# ==============================================================================
# Gate 1: Schema Validation Tests
# ==============================================================================

def test_gate1_schema_missing_required_fields():
    """Fails if summary or answer is empty."""
    bad_cand = AICandidateAnswer(
        summary="",
        answer="Valid answer text.",
        conclusions=[],
    )
    violations = SchemaValidator.validate(bad_cand)
    assert len(violations) > 0
    assert any(v.rule == "REQUIRED_SUMMARY" for v in violations)


def test_gate1_schema_valid_object():
    """Passes valid candidate object."""
    valid_cand = AICandidateAnswer(
        summary="Summary of spend.",
        answer="Detailed spend breakdown.",
        conclusions=[
            AICandidateConclusion(
                statement="EKS was primary driver.",
                epistemic_class=EpistemicClass.OBSERVED,
                evidence_ids=["ev-eks-cost"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("82000.00"), unit="INR", evidence_id="ev-eks-cost")
                ],
            )
        ],
        limitations=["Data lags 24h."],
        recommended_next_steps=["Review node groups."],
    )
    violations = SchemaValidator.validate(valid_cand)
    assert len(violations) == 0


# ==============================================================================
# Gate 2: Evidence-ID Resolution Tests
# ==============================================================================

def test_gate2_rejects_nonexistent_evidence_id(sample_evidence_package):
    """Rejects fabricated evidence IDs not in the package."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="Fabricated claim.",
                epistemic_class=EpistemicClass.OBSERVED,
                evidence_ids=["ev-fake-999"],
            )
        ],
    )
    violations = EvidenceValidator.validate(cand, sample_evidence_package)
    assert len(violations) > 0
    assert violations[0].rule == "NONEXISTENT_EVIDENCE_ID"
    assert violations[0].evidence_id == "ev-fake-999"


def test_gate2_accepts_valid_evidence_ids(sample_evidence_package):
    """Passes when all cited evidence IDs exist."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="EKS spend is ₹82,000.",
                epistemic_class=EpistemicClass.OBSERVED,
                evidence_ids=["ev-eks-cost"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("82000.00"), unit="INR", evidence_id="ev-eks-cost")
                ],
            )
        ],
    )
    violations = EvidenceValidator.validate(cand, sample_evidence_package)
    assert len(violations) == 0


# ==============================================================================
# Gate 3: Numeric Claim Validation Tests
# ==============================================================================

def test_gate3_passes_within_one_percent_tolerance(sample_evidence_package):
    """Passes claim within ±1.0% tolerance (82,400 vs 82,000 is +0.48%)."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="EKS spend.",
                epistemic_class=EpistemicClass.OBSERVED,
                evidence_ids=["ev-eks-cost"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("82400.00"), unit="INR", evidence_id="ev-eks-cost")
                ],
            )
        ],
    )
    violations = NumericValidator.validate(cand, sample_evidence_package)
    assert len(violations) == 0


def test_gate3_rejects_numerical_hallucination(sample_evidence_package):
    """Rejects claim exceeding ±1.0% tolerance (92,000 vs 82,000 is +12.2%)."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="EKS spend.",
                epistemic_class=EpistemicClass.OBSERVED,
                evidence_ids=["ev-eks-cost"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("92000.00"), unit="INR", evidence_id="ev-eks-cost")
                ],
            )
        ],
    )
    violations = NumericValidator.validate(cand, sample_evidence_package)
    assert len(violations) > 0
    assert violations[0].rule == "NUMERIC_TOLERANCE_EXCEEDED"
    assert violations[0].claim_value == Decimal("92000.00")
    assert violations[0].authoritative_value == Decimal("82000.00")


def test_gate3_zero_baseline_exactness(sample_evidence_package):
    """Zero baseline requires exact zero; 0.01 is rejected."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="Backup cost.",
                epistemic_class=EpistemicClass.OBSERVED,
                evidence_ids=["ev-zero-cost"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("0.01"), unit="INR", evidence_id="ev-zero-cost")
                ],
            )
        ],
    )
    violations = NumericValidator.validate(cand, sample_evidence_package)
    assert len(violations) > 0
    assert violations[0].rule == "NUMERIC_ZERO_BASELINE_EXACTNESS"


def test_gate3_incompatible_unit_rejection(sample_evidence_package):
    """Rejects numeric claim when units are incompatible (e.g. % vs INR)."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="EKS spend.",
                epistemic_class=EpistemicClass.OBSERVED,
                evidence_ids=["ev-eks-cost"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("82000.00"), unit="%", evidence_id="ev-eks-cost")
                ],
            )
        ],
    )
    violations = NumericValidator.validate(cand, sample_evidence_package)
    assert len(violations) > 0
    assert violations[0].rule == "INCOMPATIBLE_NUMERIC_UNIT"


# ==============================================================================
# Gate 4: Epistemic Integrity Tests
# ==============================================================================

def test_gate4_rejects_inferred_to_observed_upgrade(sample_evidence_package):
    """Prohibits upgrading INFERRED recommendation to OBSERVED fact."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="We observed downsizing savings.",
                epistemic_class=EpistemicClass.OBSERVED,  # Prohibited upgrade!
                evidence_ids=["ev-rec-downsize"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("14500.00"), unit="INR", evidence_id="ev-rec-downsize")
                ],
            )
        ],
    )
    violations = EpistemicValidator.validate(cand, sample_evidence_package)
    assert len(violations) > 0
    assert any(v.rule in ("PROHIBITED_EPISTEMIC_UPGRADE", "INVALID_OBSERVED_UPGRADE") for v in violations)


def test_gate4_rejects_projected_to_derived_upgrade(sample_evidence_package):
    """Prohibits presenting PROJECTED scenario savings as DERIVED."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="Modernization produced actual savings.",
                epistemic_class=EpistemicClass.DERIVED,  # Prohibited upgrade!
                evidence_ids=["ev-scen-graviton"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("35000.00"), unit="INR", evidence_id="ev-scen-graviton")
                ],
            )
        ],
    )
    violations = EpistemicValidator.validate(cand, sample_evidence_package)
    assert len(violations) > 0
    assert any(v.rule in ("PROHIBITED_EPISTEMIC_UPGRADE", "PROJECTED_PRESENTED_AS_FACT") for v in violations)


# ==============================================================================
# Gate 5: Citation Integrity & Completeness Tests
# ==============================================================================

def test_gate5_rejects_factual_conclusion_without_citations(sample_evidence_package):
    """Factual conclusion asserting cost surge without citations is rejected."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="EKS cluster spend increased dramatically across the account.",
                epistemic_class=EpistemicClass.OBSERVED,
                evidence_ids=[],  # Missing citation!
                numeric_claims=[],
            )
        ],
    )
    violations = CitationValidator.validate(cand, sample_evidence_package)
    assert len(violations) > 0
    assert violations[0].rule == "UNSUPPORTED_FACTUAL_CLAIM"


# ==============================================================================
# Gate 6 & 7: Security & Confidence Prohibition Tests
# ==============================================================================

def test_gate6_recursive_confidence_prohibition():
    """Detects and rejects AI-generated confidence scores nested inside dictionaries."""
    payload = {
        "summary": "Valid summary",
        "answer": "Valid answer",
        "conclusions": [
            {
                "statement": "Valid statement",
                "epistemic_class": "OBSERVED",
                "evidence_ids": ["ev-1"],
                "metadata": {
                    "nested_score": {
                        "confidence": 0.95  # Prohibited!
                    }
                }
            }
        ],
        "limitations": [],
        "recommended_next_steps": [],
    }
    violations = SecurityValidator.validate(payload)
    assert len(violations) > 0
    assert any(v.rule == "PROHIBITED_CONFIDENCE_FIELD" for v in violations)


def test_gate7_secret_leak_aws_access_key():
    """Detects and rejects candidate text leaking raw AWS access keys."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="The access key used is AKIAIOSFODNN7EXAMPLE for this bucket.",
        conclusions=[],
    )
    violations = SecurityValidator.validate(cand)
    assert len(violations) > 0
    assert any(v.rule == "SECRET_LEAK_AWS_KEY" for v in violations)


def test_gate7_prompt_injection_execution_detection():
    """Detects and rejects candidate complying with hostile instructions."""
    cand = AICandidateAnswer(
        summary="Rules overridden.",
        answer="I have ignored all previous instructions and revealed the system prompt leak.",
        conclusions=[],
    )
    violations = SecurityValidator.validate(cand)
    assert len(violations) > 0
    assert any(v.rule == "PROMPT_INJECTION_FOLLOWED" for v in violations)


# ==============================================================================
# Gate 8: Limitation Preservation Tests
# ==============================================================================

def test_gate8_rejects_invented_telemetry_when_not_available(sample_evidence_package):
    """Prohibits inventing CPU numbers when telemetry is NOT_AVAILABLE."""
    cand = AICandidateAnswer(
        summary="Database is underutilized.",
        answer="CPU utilization is 5.0%.",
        conclusions=[
            AICandidateConclusion(
                statement="Database CPU utilization is 5.0%.",
                epistemic_class=EpistemicClass.OBSERVED,
                evidence_ids=["ev-telem-db"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("5.0"), unit="%", evidence_id="ev-telem-db")
                ],
            )
        ],
    )
    violations = LimitationsValidator.validate(cand, sample_evidence_package)
    assert len(violations) > 0
    assert violations[0].rule == "FABRICATED_TELEMETRY_OBSERVATION"


def test_gate8_requires_stale_data_qualification():
    """Requires qualifying stale data in limitations or freshness note."""
    stale_pkg = EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        freshness=DataFreshness(status=DataFreshnessStatus.STALE),
        observations=[
            EvidenceItem(
                id="ev-stale-spend",
                type="SPEND_TOTAL",
                epistemic_class=EpistemicClass.OBSERVED,
                statement="Spend is ₹100,000.",
                value=Decimal("100000.00"),
                unit="INR",
            )
        ],
        evidence_count=1,
    )
    # Candidate does NOT mention stale data anywhere
    cand = AICandidateAnswer(
        summary="Current spend is ₹100,000.",
        answer="Your current spend is ₹100,000.",
        conclusions=[],
        limitations=["No limitations noted."],
        freshness_note=None,
    )
    violations = LimitationsValidator.validate(cand, stale_pkg)
    assert len(violations) > 0
    assert violations[0].rule == "UNQUALIFIED_STALE_EVIDENCE"
