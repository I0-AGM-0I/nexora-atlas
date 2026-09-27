"""
NEXORA ATLAS - AI Response Validation Result Contract (Phase 9 Milestone 4)
Defines structured validation outcomes, diagnostic violation taxonomies,
and cryptographic provenance metadata for verified answers.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field

from app.ai.models import AIAnswer, NumericClaim


VALIDATOR_VERSION = "atlas-ai-validator-v1"


class ValidationStatus(str, Enum):
    """
    Explicit taxonomy of deterministic AI validation outcomes.
    Distinguishes structural, evidentiary, mathematical, epistemic, and security failures.
    """
    VALID = "VALID"
    INVALID_SCHEMA = "INVALID_SCHEMA"
    INVALID_EVIDENCE = "INVALID_EVIDENCE"
    INVALID_NUMERIC_CLAIM = "INVALID_NUMERIC_CLAIM"
    INVALID_EPISTEMIC_CLASS = "INVALID_EPISTEMIC_CLASS"
    INVALID_CITATION = "INVALID_CITATION"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"


class ValidationViolation(BaseModel):
    """
    Diagnostic detail for a specific validation rule breach.
    Provides actionable feedback for one-shot regeneration without leaking internal machinery.
    """
    gate: str
    rule: str
    message: str
    evidence_id: Optional[str] = None
    field_path: Optional[str] = None
    claim_value: Optional[Decimal] = None
    authoritative_value: Optional[Decimal] = None


class ValidationResult(BaseModel):
    """
    Comprehensive outcome of deterministic candidate answer validation.
    `verified_answer` is present ONLY when status == ValidationStatus.VALID.
    """
    status: ValidationStatus
    is_valid: bool
    verified_answer: Optional[AIAnswer] = None
    violations: List[ValidationViolation] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validated_numeric_claims: List[NumericClaim] = Field(default_factory=list)
    validated_evidence_ids: List[str] = Field(default_factory=list)
    validation_version: str = VALIDATOR_VERSION
    evidence_hash: Optional[str] = None
    validator_metadata: Dict[str, Any] = Field(default_factory=dict)

    # Backward-compatibility property: list of error strings
    @property
    def errors(self) -> List[str]:
        return [v.message for v in self.violations]

    # Backward-compatibility property: answer alias
    @property
    def answer(self) -> Optional[AIAnswer]:
        return self.verified_answer
