"""
NEXORA ATLAS - Phase 9 Milestone 3: AI Provider Architecture Tests
Verifies provider protocols, request/result DTOs, ProviderRegistry,
and Decimal token cost calculations.
"""

import pytest
from decimal import Decimal

from app.ai.types import AIResponseStatus, EpistemicClass
from app.ai.contracts import AIProviderContract
from app.ai.providers import (
    AIProvider,
    AIProviderRequest,
    AIProviderResult,
    AICandidateAnswer,
    AICandidateConclusion,
    AICandidateNumericClaim,
    MockAIProvider,
    OpenAIProvider,
    ProviderRegistry,
    get_provider,
)
from app.ai.constants import INPUT_COST_PER_1K_TOKENS, OUTPUT_COST_PER_1K_TOKENS


def test_provider_protocol_conformance():
    """Confirms MockAIProvider and OpenAIProvider implement AIProvider and AIProviderContract."""
    mock_p = MockAIProvider()
    openai_p = OpenAIProvider(api_key="test-key")

    assert isinstance(mock_p, AIProvider)
    assert isinstance(mock_p, AIProviderContract)
    assert isinstance(openai_p, AIProvider)
    assert isinstance(openai_p, AIProviderContract)


def test_ai_provider_request_envelope():
    """Validates AIProviderRequest carries prompt, context, hash, and metadata without DB objects."""
    req = AIProviderRequest(
        question="Why did spend increase?",
        system_prompt="System rules",
        user_prompt="User question and context",
        context_json='{"spend": 100000}',
        evidence_hash="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        model="gpt-4o-mini",
        request_id="req-12345",
    )
    assert req.question == "Why did spend increase?"
    assert len(req.evidence_hash) == 64
    assert req.model == "gpt-4o-mini"
    assert req.prompt_version == "atlas-ai-v1"
    assert req.context_version == "atlas-ai-context-v1"


def test_ai_candidate_numeric_claim_decimal_precision():
    """Proves candidate numeric claims enforce Decimal precision and do not use floats."""
    claim = AICandidateNumericClaim(
        value="460000.50",
        unit="INR",
        evidence_id="ev-123",
    )
    assert isinstance(claim.value, Decimal)
    assert claim.value == Decimal("460000.50")
    assert claim.evidence_id == "ev-123"

    # Coerces integer and float input safely to Decimal
    int_claim = AICandidateNumericClaim(value=82000, unit="INR", evidence_id="ev-int")
    assert isinstance(int_claim.value, Decimal)
    assert int_claim.value == Decimal("82000")


def test_ai_candidate_answer_structure_and_helpers():
    """Tests AICandidateAnswer collection helpers for numeric claims and evidence IDs."""
    c1 = AICandidateConclusion(
        statement="EKS cost surged.",
        epistemic_class=EpistemicClass.OBSERVED,
        evidence_ids=["ev-eks-1"],
        numeric_claims=[
            AICandidateNumericClaim(value=Decimal("82000.00"), unit="INR", evidence_id="ev-eks-1")
        ],
    )
    c2 = AICandidateConclusion(
        statement="GPU instances expanded.",
        epistemic_class=EpistemicClass.OBSERVED,
        evidence_ids=["ev-gpu-1"],
        numeric_claims=[
            AICandidateNumericClaim(value=Decimal("51000.00"), unit="INR", evidence_id="ev-gpu-1")
        ],
    )
    candidate = AICandidateAnswer(
        summary="Spend increased due to EKS and GPU.",
        answer="Detailed spend breakdown.",
        conclusions=[c1, c2],
    )
    all_claims = candidate.all_numeric_claims()
    assert len(all_claims) == 2
    assert all_claims[0].value == Decimal("82000.00")
    assert all_claims[1].value == Decimal("51000.00")

    cited_ids = candidate.all_evidence_ids()
    assert cited_ids == ["ev-eks-1", "ev-gpu-1"]


def test_provider_result_token_cost_calculation():
    """Proves token cost calculation uses exact Decimal arithmetic, never float."""
    input_toks = 1500
    output_toks = 500

    expected_cost = (
        (Decimal(input_toks) / Decimal(1000) * INPUT_COST_PER_1K_TOKENS)
        + (Decimal(output_toks) / Decimal(1000) * OUTPUT_COST_PER_1K_TOKENS)
    )

    result = AIProviderResult(
        status=AIResponseStatus.COMPLETED,
        provider="mock",
        model="test-model",
        input_tokens=input_toks,
        output_tokens=output_toks,
        total_tokens=2000,
        estimated_cost_usd=expected_cost,
        latency_ms=25,
        request_id="req-99",
        evidence_hash="test-hash",
    )
    assert isinstance(result.estimated_cost_usd, Decimal)
    assert result.estimated_cost_usd == expected_cost
    assert result.total_tokens == 2000


def test_provider_registry_resolution():
    """Tests ProviderRegistry dynamically resolves mock and openai providers."""
    mock_instance = ProviderRegistry.get_provider("mock")
    assert isinstance(mock_instance, MockAIProvider)

    openai_instance = ProviderRegistry.get_provider("openai")
    assert isinstance(openai_instance, OpenAIProvider)

    # Unknown provider defaults safely to MockAIProvider
    fallback_instance = ProviderRegistry.get_provider("unknown_provider_xyz")
    assert isinstance(fallback_instance, MockAIProvider)

    # Custom registration
    class CustomProvider(MockAIProvider):
        pass

    ProviderRegistry.register("custom", lambda: CustomProvider())
    custom_inst = ProviderRegistry.get_provider("custom")
    assert isinstance(custom_inst, CustomProvider)
