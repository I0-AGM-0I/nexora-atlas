"""
NEXORA ATLAS - AI Subsystem (Phase 9)
Natural Language Explanation & Provenance-Aware Intelligence.
Strictly read-only; explains deterministic Atlas evidence contracts.
"""

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
    EvidenceItem,
    EvidencePackage,
    AIAnswer,
    AIConclusion,
    AICitation,
    NumericClaim,
    AIResponse,
    DataFreshness,
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

from app.ai.providers import (
    AIProvider,
    AIProviderRequest,
    AIProviderResult,
    AICandidateAnswer,
    AICandidateConclusion,
    AICandidateCitation,
    AICandidateNumericClaim,
    MockAIProvider,
    OpenAIProvider,
    ProviderRegistry,
    get_provider,
)
from app.ai.prompts import PromptBuilder, build_system_prompt, build_user_prompt

__all__ = [
    # Versions & Constants
    "AI_SYSTEM_VERSION",
    "PROMPT_SYSTEM_VERSION",
    "EXPLANATION_PROMPT_VERSION",
    "CONTEXT_VERSION",
    "NUMERICAL_TOLERANCE_RATIO",
    "MAX_EVIDENCE_ITEMS",
    "MAX_PERSISTED_EVIDENCE_BYTES",
    # Types & Enums
    "EpistemicClass",
    "QuestionCategory",
    "ScopeType",
    "AIResponseStatus",
    "ProviderErrorCode",
    "DataFreshnessStatus",
    "ValidationFailureReason",
    "QUESTION_CATEGORY_ALLOWED_SCOPES",
    # Domain Models
    "EvidenceItem",
    "EvidencePackage",
    "AIAnswer",
    "AIConclusion",
    "AICitation",
    "NumericClaim",
    "AIResponse",
    "DataFreshness",
    # Contracts & Boundary Protocols
    "validate_numeric_tolerance",
    "reject_prohibited_fields",
    "is_epistemic_upgrade_prohibited",
    "ValidationGateResult",
    "QueryClassifierContract",
    "EvidenceRetrieverContract",
    "AIProviderContract",
    "ContextBuilderContract",
    "ResponseValidatorContract",
    "AIInteractionAuditContract",
    # Providers & Prompts
    "AIProvider",
    "AIProviderRequest",
    "AIProviderResult",
    "AICandidateAnswer",
    "AICandidateConclusion",
    "AICandidateCitation",
    "AICandidateNumericClaim",
    "MockAIProvider",
    "OpenAIProvider",
    "ProviderRegistry",
    "get_provider",
    "PromptBuilder",
    "build_system_prompt",
    "build_user_prompt",
]

