"""
NEXORA ATLAS - Orchestration: One-Shot Controlled Regeneration (Phase 9 Milestone 4)
Builds structured regeneration prompts conveying deterministic validation failure diagnostics.
Supplies strictly bounded evidence context without exposing internal validator machinery.
"""

from typing import Optional, List
from app.ai.providers.models import AIProviderRequest, AICandidateAnswer
from app.ai.validation.result import ValidationResult, ValidationViolation, ValidationStatus


# Validation statuses eligible for one-shot regeneration
REGENERATION_ELIGIBLE_STATUSES = {
    ValidationStatus.INVALID_SCHEMA,
    ValidationStatus.INVALID_NUMERIC_CLAIM,
    ValidationStatus.INVALID_EPISTEMIC_CLASS,
    ValidationStatus.INVALID_CITATION,
    ValidationStatus.UNSUPPORTED_CLAIM,
}


def is_eligible_for_regeneration(validation_result: ValidationResult) -> bool:
    """
    Determines whether a validation failure is eligible for a regeneration attempt.
    Security violations and provider failures are never eligible for regeneration.
    """
    if validation_result.status in (ValidationStatus.SECURITY_VIOLATION, ValidationStatus.PROVIDER_FAILURE):
        return False
    return validation_result.status in REGENERATION_ELIGIBLE_STATUSES


def build_regeneration_request(
    original_request: AIProviderRequest,
    candidate: AICandidateAnswer,
    validation_result: ValidationResult,
) -> AIProviderRequest:
    """
    Constructs a controlled regeneration request for the AI provider.
    Includes deterministic feedback on why the candidate was rejected.
    Receives ONLY the original bounded context and violation feedback.
    """
    violations_text: List[str] = []
    for idx, v in enumerate(validation_result.violations, 1):
        if v.claim_value is not None and v.authoritative_value is not None:
            violations_text.append(
                f"{idx}. [{v.gate}] {v.rule}: Claimed value {v.claim_value} exceeds permitted tolerance "
                f"vs authoritative evidence value {v.authoritative_value} for evidence '{v.evidence_id}'."
            )
        elif v.evidence_id:
            violations_text.append(f"{idx}. [{v.gate}] {v.rule}: {v.message}")
        else:
            violations_text.append(f"{idx}. [{v.gate}] {v.rule}: {v.message}")

    feedback_block = (
        "\n\n<validation_feedback>\n"
        "Your previous response failed deterministic Atlas validation for the following reasons:\n"
        + "\n".join(violations_text)
        + "\n\nCRITICAL INSTRUCTIONS FOR REGENERATION:\n"
        "1. Correct the candidate using ONLY the supplied authoritative evidence in <atlas_context>.\n"
        "2. Do NOT invent, assume, or fabricate any replacement numbers or citations.\n"
        "3. Preserve the exact epistemic classes (OBSERVED, DERIVED, INFERRED, PROJECTED, NOT_AVAILABLE).\n"
        "4. Respond with valid JSON matching the required schema.\n"
        "</validation_feedback>"
    )

    regen_user_prompt = f"{original_request.user_prompt}\n{feedback_block}"

    return AIProviderRequest(
        question=original_request.question,
        system_prompt=original_request.system_prompt,
        user_prompt=regen_user_prompt,
        context_json=original_request.context_json,
        bounded_context=original_request.bounded_context,
        evidence_hash=original_request.evidence_hash,
        prompt_version=original_request.prompt_version,
        context_version=original_request.context_version,
        model=original_request.model,
        request_id=f"{original_request.request_id}-regen",
        temperature=original_request.temperature,
        max_tokens=original_request.max_tokens,
    )
