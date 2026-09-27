"""
NEXORA ATLAS - AI Domain Contracts & Boundary Protocols (Phase 9)
Defines lightweight typing Protocols, epistemic invariants, numeric tolerance contracts,
and recursive prohibition rules for the AI natural language interrogation subsystem.

Architectural Principles:
- Deterministic Atlas engines decide what the evidence says.
- The AI layer explains that evidence to the user.
- Authorization is strictly enforced before query classification.
- Classification is a routing mechanism, NOT a security boundary.
- ±1.0% numerical validation is a precision tolerance, NOT an AI confidence score.
"""

from typing import Protocol, runtime_checkable, Optional, Dict, Any, List, Set, Union
from decimal import Decimal
from dataclasses import dataclass, field

from app.ai.constants import NUMERICAL_TOLERANCE_RATIO
from app.ai.types import (
    EpistemicClass,
    ScopeType,
    QuestionCategory,
    ValidationFailureReason,
    QUESTION_CATEGORY_ALLOWED_SCOPES,
)
from app.ai.models import EvidencePackage, AIAnswer, AIResponse


# ==============================================================================
# 1. NUMERIC TOLERANCE CONTRACT
# ==============================================================================

def validate_numeric_tolerance(
    claim_val: Union[Decimal, float, int, str],
    authoritative_val: Union[Decimal, float, int, str],
    tolerance_ratio: Decimal = NUMERICAL_TOLERANCE_RATIO,
) -> bool:
    """
    Validates a claim value against an authoritative Atlas value with Decimal precision.

    Contract:
      absolute_error = |C - A|
      allowed_error  = |A| * tolerance_ratio
      PASS if: absolute_error <= allowed_error

    Zero-Baseline Invariant:
      If authoritative A == 0: exact zero is strictly required (claim == 0).
      Percentage-based tolerance is undefined on zero baselines.

    Note: ±1.0% is a verification tolerance, NOT an AI confidence score.
    """
    claim_dec = Decimal(str(claim_val)) if not isinstance(claim_val, Decimal) else claim_val
    auth_dec = Decimal(str(authoritative_val)) if not isinstance(authoritative_val, Decimal) else authoritative_val

    if auth_dec == Decimal("0"):
        return claim_dec == Decimal("0")

    abs_error = abs(claim_dec - auth_dec)
    allowed_error = abs(auth_dec) * tolerance_ratio
    return abs_error <= allowed_error


# ==============================================================================
# 2. PROHIBITED AI FIELD DETECTION (RECURSIVE)
# ==============================================================================

DEFAULT_PROHIBITED_AI_KEYS: Set[str] = {"confidence"}


def reject_prohibited_fields(
    payload: Any,
    prohibited_keys: Optional[Set[str]] = None,
    path: str = "root",
) -> List[str]:
    """
    Recursively inspects parsed AI payload (dictionaries, lists, primitives)
    for prohibited keys, specifically any field named 'confidence'.

    Enterprise Invariant:
      Atlas deterministic confidence is authoritative evidence.
      AI-generated confidence scores are strictly prohibited across all nesting levels.
    """
    targets = prohibited_keys or DEFAULT_PROHIBITED_AI_KEYS
    violations: List[str] = []

    if isinstance(payload, dict):
        for k, v in payload.items():
            current_path = f"{path}.{k}"
            if k in targets:
                violations.append(
                    f"AI-generated confidence score detected at '{current_path}'; prohibited by Atlas contract."
                )
            violations.extend(reject_prohibited_fields(v, targets, current_path))
    elif isinstance(payload, list):
        for idx, item in enumerate(payload):
            violations.extend(reject_prohibited_fields(item, targets, f"{path}[{idx}]"))

    return violations


# ==============================================================================
# 3. EPISTEMIC BOUNDARY & UPGRADE PROHIBITION RULES
# ==============================================================================

# Explicit Epistemic Boundary Hierarchy:
# OBSERVED   : Directly recorded by Atlas sensors/APIs (e.g. AWS Cost Explorer, CloudWatch)
# DERIVED    : Mathematically calculated from authoritative observations
# INFERRED   : Deterministic Atlas interpretation supported by evidence (e.g. rightsizing)
# ASSUMED    : Explicit scenario/input assumption (e.g. 50% target utilization)
# PROJECTED  : Future-state or scenario outcome
# NOT_AVAILABLE: Evidence required to make the claim does not exist

PROHIBITED_EPISTEMIC_UPGRADES: Set[tuple[EpistemicClass, EpistemicClass]] = {
    # (Claimed / Elevated Class, Underlying Evidence Class)
    (EpistemicClass.OBSERVED, EpistemicClass.INFERRED),
    (EpistemicClass.OBSERVED, EpistemicClass.PROJECTED),
    (EpistemicClass.OBSERVED, EpistemicClass.ASSUMED),
    (EpistemicClass.OBSERVED, EpistemicClass.NOT_AVAILABLE),
    (EpistemicClass.DERIVED, EpistemicClass.PROJECTED),
    (EpistemicClass.DERIVED, EpistemicClass.NOT_AVAILABLE),
    (EpistemicClass.INFERRED, EpistemicClass.NOT_AVAILABLE),
    (EpistemicClass.ASSUMED, EpistemicClass.NOT_AVAILABLE),
    (EpistemicClass.PROJECTED, EpistemicClass.NOT_AVAILABLE),
}


def is_epistemic_upgrade_prohibited(
    claimed_class: EpistemicClass,
    evidence_class: EpistemicClass,
) -> bool:
    """
    Evaluates whether an AI explanation is illegally elevating the certainty
    or epistemic standing of an underlying evidence item.

    Example:
      Presenting an INFERRED rightsizing candidate as an OBSERVED fact is prohibited.
      Presenting a PROJECTED scenario outcome as a DERIVED calculation is prohibited.
      Presenting a NOT_AVAILABLE missing data state as an OBSERVED fact is prohibited.
    """
    if (claimed_class, evidence_class) in PROHIBITED_EPISTEMIC_UPGRADES:
        return True
    return False


# ==============================================================================
# 4. VALIDATION GATE CONTRACTS
# ==============================================================================

@dataclass
class ValidationGateResult:
    """Carries the outcome of deterministic validation across all four gates."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    failure_reasons: List[ValidationFailureReason] = field(default_factory=list)
    answer: Optional[AIAnswer] = None


# ==============================================================================
# 5. LIGHTWEIGHT PROTOCOLS (ABCs WITHOUT HEAVY HIERARCHIES)
# ==============================================================================

@runtime_checkable
class QueryClassifierContract(Protocol):
    """
    Contract for natural language query classification.
    Routing mechanism only: TenantContext authorization MUST be performed
    strictly prior to invoking classification.
    """
    def classify_question(self, question: str) -> QuestionCategory:
        """Classifies a user query into one of the 13 canonical QuestionCategories."""
        ...


@runtime_checkable
class EvidenceRetrieverContract(Protocol):
    """
    Contract for deterministic evidence gathering.
    Evidence retrieval operates strictly on pre-authorized scopes.
    """
    async def retrieve(
        self,
        tenant: Any,
        scope_type: ScopeType,
        scope_id: Optional[str],
        question_category: QuestionCategory,
    ) -> EvidencePackage:
        """Retrieves and packages tenant-scoped deterministic evidence."""
        ...


@runtime_checkable
class AIProviderContract(Protocol):
    """
    Contract for AI model providers.
    Providers receive budgeted evidence and produce raw or parsed structured output.
    Providers have zero direct database access.
    """
    async def generate_explanation(
        self,
        evidence_package: EvidencePackage,
        user_question: str,
        session_context: Optional[List[Dict[str, str]]] = None,
    ) -> AIResponse:
        """Generates an explanation envelope for the given evidence package and question."""
        ...


@runtime_checkable
class ContextBuilderContract(Protocol):
    """
    Contract for evidence context preparation, budgeting, and hashing.
    """
    async def build_context(
        self,
        tenant: Any,
        scope_type: ScopeType,
        scope_id: Optional[str],
        question: str,
    ) -> EvidencePackage:
        """Assembles, sanitizes, budgets, and hashes the canonical evidence package."""
        ...


@runtime_checkable
class ResponseValidatorContract(Protocol):
    """
    Contract for deterministic validation gates.
    Authoritatively enforces zero numerical hallucinations and epistemic fidelity.
    """
    def validate(
        self,
        raw_payload: Dict[str, Any],
        evidence_package: EvidencePackage,
    ) -> ValidationGateResult:
        """Executes all 4 deterministic validation gates on candidate output."""
        ...


@runtime_checkable
class AIInteractionAuditContract(Protocol):
    """
    Contract for persisting immutable audit records of AI interactions.
    Persists evidence IDs and SHA-256 hash; avoids duplicating entire datastores.
    """
    async def record_interaction(
        self,
        organization_id: str,
        session_id: str,
        question: str,
        question_category: str,
        scope_type: str,
        scope_id: Optional[str],
        evidence_hash: str,
        evidence_ids: List[str],
        response_status: str,
        answer_json: Optional[Dict[str, Any]] = None,
        sanitized_evidence_preview: Optional[Dict[str, Any]] = None,
        latency_ms: int = 0,
        input_token_count: int = 0,
        output_token_count: int = 0,
        estimated_cost_usd: Decimal = Decimal("0.0"),
        evidence_count: int = 0,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Any:
        """Stores an auditable interaction record."""
        ...
