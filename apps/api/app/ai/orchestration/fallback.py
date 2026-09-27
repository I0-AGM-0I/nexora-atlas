"""
NEXORA ATLAS - Orchestration: Safe Failure & Deterministic Fallback (Phase 9 Milestone 4)
Handles unrecoverable validation rejections, provider outages, and deterministic fallbacks.
Guarantees rejected candidates, hallucinations, and credentials never leak to the user.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal

from app.ai.types import AIResponseStatus, ProviderErrorCode, EpistemicClass
from app.ai.models import EvidencePackage, AIResponse, AIAnswer, AIConclusion, NumericClaim, AICitation
from app.ai.providers.models import AIProviderResult
from app.ai.validation.result import ValidationResult, ValidationStatus


SAFE_FAILURE_EXPLANATION = "Atlas could not produce a verified explanation from the available evidence."


def build_safe_failure(
    validation_result: ValidationResult,
    provider_result: Optional[AIProviderResult] = None,
    regeneration_count: int = 0,
) -> AIResponse:
    """
    Constructs a safe failure response when candidate validation fails.
    The unverified candidate answer is strictly omitted (answer=None).
    """
    error_summary = "; ".join(validation_result.errors) if validation_result.errors else "Validation gate rejection."

    input_tokens = provider_result.input_tokens if provider_result else 0
    output_tokens = provider_result.output_tokens if provider_result else 0
    latency_ms = provider_result.latency_ms if provider_result else 0
    cost = provider_result.estimated_cost_usd if provider_result else Decimal("0.0")

    return AIResponse(
        status=AIResponseStatus.VALIDATION_FAILED,
        answer=None,
        raw_text=SAFE_FAILURE_EXPLANATION,
        error_code=None,
        error_message=f"Candidate answer rejected by Atlas validation gate: {error_summary}",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        estimated_cost_usd=cost,
    )


def build_provider_failure(
    provider_result: AIProviderResult,
) -> AIResponse:
    """
    Constructs a failure response when the AI provider experiences an outage, timeout, or auth error.
    Does NOT pass through candidate validation.
    """
    status = AIResponseStatus.PROVIDER_ERROR
    if provider_result.error_code == ProviderErrorCode.RATE_LIMIT:
        status = AIResponseStatus.RATE_LIMITED

    return AIResponse(
        status=status,
        answer=None,
        raw_text=None,
        error_code=provider_result.error_code,
        error_message=provider_result.error_message or "AI provider encountered an error.",
        input_tokens=provider_result.input_tokens,
        output_tokens=provider_result.output_tokens,
        latency_ms=provider_result.latency_ms,
        estimated_cost_usd=provider_result.estimated_cost_usd,
    )


def build_deterministic_fallback(
    evidence_package: EvidencePackage,
    reason: str = "AI explanation unavailable; displaying deterministic Atlas finding.",
) -> AIResponse:
    """
    Provides a deterministic Atlas finding directly from the evidence package
    when AI is disabled, unconfigured, or unavailable.
    Explicitly labeled as deterministic Atlas source, NEVER pretended to be AI output.
    """
    conclusions: List[AIConclusion] = []
    numeric_claims: List[NumericClaim] = []

    # Assemble factual observations directly from package
    for item in evidence_package.observations[:3]:
        claims = []
        if item.value is not None:
            nc = NumericClaim(
                value=item.value,
                unit=item.unit or "INR",
                evidence_id=item.id,
                evidence_ids=[item.id],
            )
            claims.append(nc)
            numeric_claims.append(nc)

        conclusions.append(
            AIConclusion(
                statement=item.statement,
                epistemic_class=item.epistemic_class,
                evidence_ids=[item.id],
                numeric_claims=claims,
            )
        )

    summary = (
        f"Deterministic Atlas finding based on {len(evidence_package.all_items())} authoritative evidence items."
    )
    answer_text = (
        f"{reason}\n\n"
        + "Authoritative observations from Atlas sensors:\n"
        + "\n".join([f"- {c.statement}" for c in conclusions])
    )

    verified_answer = AIAnswer(
        summary=summary,
        answer=answer_text,
        conclusions=conclusions,
        limitations=list(evidence_package.limitations),
        recommended_next_steps=["Inspect detailed telemetry in Atlas Command Center."],
        cited_entities=[],
        epistemic_notes=["Direct deterministic Atlas extraction; zero AI generation."],
        freshness_note=evidence_package.freshness.freshness_summary if evidence_package.freshness else None,
    )

    return AIResponse(
        status=AIResponseStatus.COMPLETED,
        answer=verified_answer,
        raw_text=answer_text,
        error_code=None,
        error_message=None,
        input_tokens=0,
        output_tokens=0,
        latency_ms=0,
        estimated_cost_usd=Decimal("0.0"),
    )
