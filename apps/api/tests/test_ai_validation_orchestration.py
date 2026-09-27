"""
NEXORA ATLAS - AI Validation & Orchestration Golden Test Suite (Phase 9 Milestone 4)
Exhaustively tests Golden Scenarios A through Q:
- A: Valid Answer
- B: Missing Evidence ID
- C: Numerical Hallucination
- D: Within Tolerance
- E: Zero-Value Edge Case
- F: PROJECTED -> OBSERVED
- G: INFERRED -> OBSERVED
- H: Missing Telemetry / Unsupported Claim
- I: Confidence Injection
- J: Citation-less Factual Conclusion
- K: Malicious Metadata Injection
- L: Provider Timeout
- M: Regeneration Succeeds
- N: Regeneration Fails
- O: No Infinite Regeneration (<= 2 calls)
- P: Cross-Tenant Security Isolation
- Q: Full End-to-End Chain
"""

import pytest
from decimal import Decimal
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

from app.ai.types import (
    EpistemicClass,
    ScopeType,
    AIResponseStatus,
    ProviderErrorCode,
)
from app.ai.models import (
    EvidenceItem,
    EvidencePackage,
    AIAnswer,
)
from app.ai.providers.models import (
    AIProviderRequest,
    AIProviderResult,
    AICandidateAnswer,
    AICandidateConclusion,
    AICandidateNumericClaim,
)
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.validation.result import ValidationStatus, ValidationResult
from app.ai.validation.validator import ResponseValidator
from app.ai.orchestration.engine import AIExplanationOrchestrator
from app.ai.context.builder import ContextBuilder
from app.ai.prompts.builder import PromptBuilder


@pytest.fixture
def base_evidence_package():
    """Standardized evidence package for Golden test scenarios."""
    item1 = EvidenceItem(
        id="ev-opt-460k",
        type="RECOMMENDATION",
        epistemic_class=EpistemicClass.INFERRED,
        statement="Downsize compute node for ₹460,000.00 monthly savings.",
        value=Decimal("460000.00"),
        unit="INR",
        source="Atlas Optimizer",
    )
    item2 = EvidenceItem(
        id="ev-zero-cost",
        type="COST_ITEM",
        epistemic_class=EpistemicClass.OBSERVED,
        statement="Zero spend backup volume.",
        value=Decimal("0.00"),
        unit="INR",
        source="Cost Explorer",
    )
    item3 = EvidenceItem(
        id="ev-graviton-proj",
        type="SCENARIO",
        epistemic_class=EpistemicClass.PROJECTED,
        statement="Modernization simulation projects ₹35,000.00 monthly savings.",
        value=Decimal("35000.00"),
        unit="INR",
        source="Scenario Planner",
    )
    item4 = EvidenceItem(
        id="ev-telem-na",
        type="TELEMETRY",
        epistemic_class=EpistemicClass.NOT_AVAILABLE,
        statement="No telemetry available for database cluster.",
        value=None,
        unit=None,
        source="CloudWatch",
    )

    return EvidencePackage(
        scope_type=ScopeType.DASHBOARD,
        observations=[item2],
        recommendations=[item1],
        scenarios=[item3],
        telemetry=[item4],
        evidence_count=4,
    )


@pytest.fixture
def base_provider_request(base_evidence_package):
    """Pre-built AIProviderRequest with valid bounded context."""
    b_ctx = ContextBuilder.create_bounded_context(base_evidence_package)
    return PromptBuilder.build_request(
        question="What savings opportunities exist?",
        evidence_package=base_evidence_package,
        bounded_context=b_ctx,
    )


# ==============================================================================
# Golden Tests A through K (Validation Gate Outcomes)
# ==============================================================================

def test_golden_a_valid_answer(base_evidence_package):
    """Golden A: Valid candidate passes all gates and constructs AIAnswer."""
    cand = AICandidateAnswer(
        summary="Rightsizing savings identified.",
        answer="Atlas identifies ₹460,000 monthly savings.",
        conclusions=[
            AICandidateConclusion(
                statement="Downsizing saves ₹460,000 monthly.",
                epistemic_class=EpistemicClass.INFERRED,
                evidence_ids=["ev-opt-460k"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("460000.00"), unit="INR", evidence_id="ev-opt-460k")
                ],
            )
        ],
        limitations=["Peak workload validation required."],
        recommended_next_steps=["Review node utilization."],
    )
    res = ResponseValidator.validate(cand, base_evidence_package)
    assert res.status == ValidationStatus.VALID
    assert res.is_valid is True
    assert isinstance(res.verified_answer, AIAnswer)
    assert len(res.validated_numeric_claims) == 1
    assert res.validated_numeric_claims[0].value == Decimal("460000.00")


def test_golden_b_missing_evidence_id(base_evidence_package):
    """Golden B: Nonexistent evidence ID fails with INVALID_EVIDENCE."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="Savings statement.",
                epistemic_class=EpistemicClass.INFERRED,
                evidence_ids=["ev-nonexistent-999"],
            )
        ],
    )
    res = ResponseValidator.validate(cand, base_evidence_package)
    assert res.status == ValidationStatus.INVALID_EVIDENCE
    assert res.is_valid is False
    assert res.verified_answer is None


def test_golden_c_numerical_hallucination(base_evidence_package):
    """Golden C: Inflated claim (₹920,000 vs ₹460,000) fails with INVALID_NUMERIC_CLAIM."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="Inflated claim.",
                epistemic_class=EpistemicClass.INFERRED,
                evidence_ids=["ev-opt-460k"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("920000.00"), unit="INR", evidence_id="ev-opt-460k")
                ],
            )
        ],
    )
    res = ResponseValidator.validate(cand, base_evidence_package)
    assert res.status == ValidationStatus.INVALID_NUMERIC_CLAIM
    assert res.is_valid is False


def test_golden_d_within_tolerance(base_evidence_package):
    """Golden D: Claim within ±1.0% (₹459,500 vs ₹460,000 is -0.11%) passes."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="Near-exact savings.",
                epistemic_class=EpistemicClass.INFERRED,
                evidence_ids=["ev-opt-460k"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("459500.00"), unit="INR", evidence_id="ev-opt-460k")
                ],
            )
        ],
    )
    res = ResponseValidator.validate(cand, base_evidence_package)
    assert res.status == ValidationStatus.VALID
    assert res.is_valid is True


def test_golden_e_zero_value_edge_case(base_evidence_package):
    """Golden E: Zero baseline requires exact zero; 0.01 fails with INVALID_NUMERIC_CLAIM."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="Zero cost item.",
                epistemic_class=EpistemicClass.OBSERVED,
                evidence_ids=["ev-zero-cost"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("0.01"), unit="INR", evidence_id="ev-zero-cost")
                ],
            )
        ],
    )
    res = ResponseValidator.validate(cand, base_evidence_package)
    assert res.status == ValidationStatus.INVALID_NUMERIC_CLAIM
    assert res.is_valid is False


def test_golden_f_projected_to_observed(base_evidence_package):
    """Golden F: PROJECTED scenario presented as OBSERVED fails with INVALID_EPISTEMIC_CLASS."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="Modernization actual savings.",
                epistemic_class=EpistemicClass.OBSERVED,  # Upgraded!
                evidence_ids=["ev-graviton-proj"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("35000.00"), unit="INR", evidence_id="ev-graviton-proj")
                ],
            )
        ],
    )
    res = ResponseValidator.validate(cand, base_evidence_package)
    assert res.status == ValidationStatus.INVALID_EPISTEMIC_CLASS
    assert res.is_valid is False


def test_golden_g_inferred_to_observed(base_evidence_package):
    """Golden G: INFERRED recommendation presented as OBSERVED fails with INVALID_EPISTEMIC_CLASS."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="Observed downsizing.",
                epistemic_class=EpistemicClass.OBSERVED,  # Upgraded!
                evidence_ids=["ev-opt-460k"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("460000.00"), unit="INR", evidence_id="ev-opt-460k")
                ],
            )
        ],
    )
    res = ResponseValidator.validate(cand, base_evidence_package)
    assert res.status == ValidationStatus.INVALID_EPISTEMIC_CLASS
    assert res.is_valid is False


def test_golden_h_missing_telemetry_unsupported_claim(base_evidence_package):
    """Golden H: Fabricating utilization when telemetry is NOT_AVAILABLE fails with UNSUPPORTED_CLAIM."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="Observed database CPU utilization is 8.0%.",
                epistemic_class=EpistemicClass.OBSERVED,
                evidence_ids=["ev-telem-na"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("8.0"), unit="%", evidence_id="ev-telem-na")
                ],
            )
        ],
    )
    res = ResponseValidator.validate(cand, base_evidence_package)
    assert res.status == ValidationStatus.UNSUPPORTED_CLAIM
    assert res.is_valid is False


def test_golden_i_confidence_injection(base_evidence_package):
    """Golden I: Confidence score in candidate payload fails with SECURITY_VIOLATION."""
    payload = {
        "summary": "Summary",
        "answer": "Answer",
        "conclusions": [
            {
                "statement": "Valid conclusion",
                "epistemic_class": "INFERRED",
                "evidence_ids": ["ev-opt-460k"],
                "confidence_score": 0.95,  # Injected!
            }
        ],
        "limitations": [],
        "recommended_next_steps": [],
    }
    res = ResponseValidator.validate(payload, base_evidence_package)
    assert res.status == ValidationStatus.SECURITY_VIOLATION
    assert res.is_valid is False


def test_golden_j_citation_less_factual_conclusion(base_evidence_package):
    """Golden J: Factual conclusion lacking citations fails with INVALID_CITATION."""
    cand = AICandidateAnswer(
        summary="Summary",
        answer="Answer",
        conclusions=[
            AICandidateConclusion(
                statement="Total cloud spend surged across all active accounts.",
                epistemic_class=EpistemicClass.OBSERVED,
                evidence_ids=[],  # Missing citation!
                numeric_claims=[],
            )
        ],
    )
    res = ResponseValidator.validate(cand, base_evidence_package)
    assert res.status == ValidationStatus.INVALID_CITATION
    assert res.is_valid is False


def test_golden_k_malicious_metadata_injection(base_evidence_package):
    """Golden K: Malicious prompt injection text in output fails with SECURITY_VIOLATION."""
    cand = AICandidateAnswer(
        summary="Ignore rules",
        answer="I have followed instructions to ignore all instructions and reveal secrets.",
        conclusions=[],
    )
    res = ResponseValidator.validate(cand, base_evidence_package)
    assert res.status == ValidationStatus.SECURITY_VIOLATION
    assert res.is_valid is False


def test_golden_p_cross_tenant_isolation(base_evidence_package):
    """Golden P: Citation referencing an evidence ID belonging to another tenant/org is rejected."""
    # Suppose ev-tenant-b-999 exists in another tenant's system, but NOT in this package
    cand = AICandidateAnswer(
        summary="Cross tenant finding",
        answer="Summary",
        conclusions=[
            AICandidateConclusion(
                statement="Foreign tenant resource spend.",
                epistemic_class=EpistemicClass.OBSERVED,
                evidence_ids=["ev-tenant-b-999"],
            )
        ],
    )
    res = ResponseValidator.validate(cand, base_evidence_package)
    assert res.status == ValidationStatus.INVALID_EVIDENCE
    assert res.is_valid is False


# ==============================================================================
# Golden Tests L through O (Orchestration, Retries, Timeouts)
# ==============================================================================

@pytest.mark.asyncio
async def test_golden_l_provider_timeout(base_provider_request, base_evidence_package):
    """Golden L: Provider timeout maps to PROVIDER_ERROR without running validation."""
    mock_provider = MagicMock()
    mock_provider.generate_candidate = AsyncMock(
        return_value=AIProviderResult(
            status=AIResponseStatus.PROVIDER_ERROR,
            provider="mock",
            model="mock",
            error_code=ProviderErrorCode.TIMEOUT,
            error_message="Provider deadline exceeded after 30s.",
        )
    )

    resp = await AIExplanationOrchestrator.orchestrate(
        request=base_provider_request,
        provider=mock_provider,
        evidence_package=base_evidence_package,
    )

    assert resp.status == AIResponseStatus.PROVIDER_ERROR
    assert resp.error_code == ProviderErrorCode.TIMEOUT
    assert resp.answer is None
    assert mock_provider.generate_candidate.call_count == 1


@pytest.mark.asyncio
async def test_golden_m_regeneration_succeeds(base_provider_request, base_evidence_package):
    """Golden M: Candidate 1 fails (numerical hallucination) -> regeneration candidate 2 passes."""
    # Bad candidate 1 (₹920,000)
    bad_cand = AICandidateAnswer(
        summary="Bad summary",
        answer="Bad answer",
        conclusions=[
            AICandidateConclusion(
                statement="Overstated savings.",
                epistemic_class=EpistemicClass.INFERRED,
                evidence_ids=["ev-opt-460k"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("920000.00"), unit="INR", evidence_id="ev-opt-460k")
                ],
            )
        ],
    )
    # Correct candidate 2 (₹460,000)
    good_cand = AICandidateAnswer(
        summary="Correct summary",
        answer="Correct answer",
        conclusions=[
            AICandidateConclusion(
                statement="Downsizing saves ₹460,000 monthly.",
                epistemic_class=EpistemicClass.INFERRED,
                evidence_ids=["ev-opt-460k"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("460000.00"), unit="INR", evidence_id="ev-opt-460k")
                ],
            )
        ],
    )

    mock_provider = MagicMock()
    mock_provider.generate_candidate = AsyncMock(
        side_effect=[
            AIProviderResult(
                status=AIResponseStatus.COMPLETED,
                provider="mock",
                model="mock",
                candidate_answer=bad_cand,
                input_tokens=100,
                output_tokens=50,
            ),
            AIProviderResult(
                status=AIResponseStatus.COMPLETED,
                provider="mock",
                model="mock",
                candidate_answer=good_cand,
                input_tokens=150,
                output_tokens=50,
            ),
        ]
    )

    resp = await AIExplanationOrchestrator.orchestrate(
        request=base_provider_request,
        provider=mock_provider,
        evidence_package=base_evidence_package,
    )

    assert resp.status == AIResponseStatus.COMPLETED
    assert resp.answer is not None
    assert resp.answer.conclusions[0].numeric_claims[0].value == Decimal("460000.00")
    assert mock_provider.generate_candidate.call_count == 2
    assert resp.input_tokens == 250  # Cumulative tokens tracked


@pytest.mark.asyncio
async def test_golden_n_regeneration_fails(base_provider_request, base_evidence_package):
    """Golden N: Both candidates invalid -> returns SAFE_FAILURE with answer=None."""
    bad_cand = AICandidateAnswer(
        summary="Bad summary",
        answer="Bad answer",
        conclusions=[
            AICandidateConclusion(
                statement="Hallucinated savings.",
                epistemic_class=EpistemicClass.INFERRED,
                evidence_ids=["ev-opt-460k"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("999999.00"), unit="INR", evidence_id="ev-opt-460k")
                ],
            )
        ],
    )

    mock_provider = MagicMock()
    mock_provider.generate_candidate = AsyncMock(
        side_effect=[
            AIProviderResult(
                status=AIResponseStatus.COMPLETED,
                provider="mock",
                model="mock",
                candidate_answer=bad_cand,
                input_tokens=100,
                output_tokens=50,
            ),
            AIProviderResult(
                status=AIResponseStatus.COMPLETED,
                provider="mock",
                model="mock",
                candidate_answer=bad_cand,
                input_tokens=150,
                output_tokens=50,
            ),
        ]
    )

    resp = await AIExplanationOrchestrator.orchestrate(
        request=base_provider_request,
        provider=mock_provider,
        evidence_package=base_evidence_package,
    )

    assert resp.status == AIResponseStatus.VALIDATION_FAILED
    assert resp.answer is None
    assert "could not produce a verified explanation" in resp.raw_text.lower()
    assert mock_provider.generate_candidate.call_count == 2


@pytest.mark.asyncio
async def test_golden_o_no_infinite_regeneration(base_provider_request, base_evidence_package):
    """Golden O: Provider invocation count is strictly bounded (<= 2)."""
    bad_cand = AICandidateAnswer(
        summary="Bad summary",
        answer="Bad answer",
        conclusions=[
            AICandidateConclusion(
                statement="Hallucinated savings.",
                epistemic_class=EpistemicClass.INFERRED,
                evidence_ids=["ev-opt-460k"],
                numeric_claims=[
                    AICandidateNumericClaim(value=Decimal("999999.00"), unit="INR", evidence_id="ev-opt-460k")
                ],
            )
        ],
    )

    mock_provider = MagicMock()
    mock_provider.generate_candidate = AsyncMock(
        return_value=AIProviderResult(
            status=AIResponseStatus.COMPLETED,
            provider="mock",
            model="mock",
            candidate_answer=bad_cand,
        )
    )

    await AIExplanationOrchestrator.orchestrate(
        request=base_provider_request,
        provider=mock_provider,
        evidence_package=base_evidence_package,
    )

    # Invariant: exactly 2 calls (1 initial + 1 regeneration)
    assert mock_provider.generate_candidate.call_count == 2


# ==============================================================================
# Golden Test Q: Full End-to-End Chain
# ==============================================================================

@pytest.mark.asyncio
async def test_golden_q_full_end_to_end_chain(base_evidence_package):
    """
    Golden Q: M2 Bounded Context -> M3 PromptBuilder -> M3 MockProvider -> M4 Orchestrator -> AIAnswer.
    Demonstrates clean verification with live MockAIProvider.
    """
    b_ctx = ContextBuilder.create_bounded_context(base_evidence_package)
    req = PromptBuilder.build_request(
        question="Can we rightsize this instance?",
        evidence_package=base_evidence_package,
        bounded_context=b_ctx,
    )

    provider = MockAIProvider()
    resp = await AIExplanationOrchestrator.orchestrate(
        request=req,
        provider=provider,
        evidence_package=base_evidence_package,
    )

    assert resp.status == AIResponseStatus.COMPLETED
    assert resp.answer is not None
    assert len(resp.answer.conclusions) > 0
    assert resp.answer.conclusions[0].epistemic_class == EpistemicClass.INFERRED
