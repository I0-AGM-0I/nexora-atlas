"""
NEXORA ATLAS - AI Response Validator Compatibility Adapter (Phase 9 Milestone 4)
Re-exports and routes calls to the modular app.ai.validation.validator.ResponseValidator.
Preserves backward compatibility for all existing test suites and services.
"""

from typing import List, Optional, Dict, Any, Union
from app.ai.models import EvidencePackage, AIAnswer
from app.ai.validation.validator import ResponseValidator
from app.ai.validation.result import ValidationResult as ModularValidationResult, ValidationStatus


# Re-export classes so existing imports continue working
class ValidationResult:
    """Carries the outcome of deterministic validation with backward-compatible attributes."""
    def __init__(
        self,
        is_valid: bool,
        errors: List[str],
        answer: Optional[AIAnswer] = None,
        status: Optional[ValidationStatus] = None,
    ):
        self.is_valid = is_valid
        self.errors = errors
        self.answer = answer
        self.status = status or (ValidationStatus.VALID if is_valid else ValidationStatus.INVALID_SCHEMA)


class AIResponseValidator:
    """
    Backward-compatible validator routing directly to modular ResponseValidator.
    """

    @classmethod
    def validate(
        cls,
        raw_payload: Union[Dict[str, Any], Any],
        evidence_package: EvidencePackage,
    ) -> ValidationResult:
        res: ModularValidationResult = ResponseValidator.validate(raw_payload, evidence_package)
        return ValidationResult(
            is_valid=res.is_valid,
            errors=res.errors,
            answer=res.verified_answer,
            status=res.status,
        )
