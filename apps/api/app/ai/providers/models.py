"""
NEXORA ATLAS - AI Provider Models & Candidate DTOs (Phase 9 Milestone 3)
Defines provider request, result, and untrusted candidate answer representations.
Preserves explicit separation: Provider output is an UNTRUSTED Candidate, NOT a verified Atlas answer.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from app.ai.types import EpistemicClass, AIResponseStatus
from app.ai.models import BoundedContext
from app.ai.providers.errors import ProviderErrorCode
from app.ai.constants import (
    PROMPT_SYSTEM_VERSION,
    CONTEXT_VERSION,
)


class AICandidateNumericClaim(BaseModel):
    """
    Candidate numeric claim emitted by the AI provider.
    Tied directly to an evidence ID for machine validation by M4.
    """
    value: Decimal
    unit: str
    evidence_id: str

    @field_validator("value", mode="before")
    @classmethod
    def _coerce_decimal(cls, v: Any) -> Decimal:
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class AICandidateConclusion(BaseModel):
    """
    Candidate conclusion emitted by the AI provider.
    Carries candidate epistemic class, cited evidence IDs, and numeric claims.
    """
    statement: str
    epistemic_class: EpistemicClass
    evidence_ids: List[str] = Field(default_factory=list)
    numeric_claims: List[AICandidateNumericClaim] = Field(default_factory=list)


class AICandidateCitation(BaseModel):
    """Candidate entity citation emitted by the AI provider."""
    id: str
    title: str
    entity_type: str
    entity_id: str
    link_path: Optional[str] = None


class AICandidateAnswer(BaseModel):
    """
    UNTRUSTED candidate explanation output emitted by an AI provider.
    M3 produces this candidate; M4 authoritatively decides whether it is acceptable.
    """
    summary: str = ""
    answer: str = ""
    conclusions: List[AICandidateConclusion] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    cited_entities: List[AICandidateCitation] = Field(default_factory=list)
    epistemic_notes: List[str] = Field(default_factory=list)
    freshness_note: Optional[str] = None
    raw_json: Optional[Dict[str, Any]] = None

    def all_numeric_claims(self) -> List[AICandidateNumericClaim]:
        """Collects all numeric claims across all conclusions."""
        claims = []
        for c in self.conclusions:
            claims.extend(c.numeric_claims)
        return claims

    def all_evidence_ids(self) -> List[str]:
        """Collects all unique evidence IDs cited across all conclusions and claims."""
        ids = set()
        for c in self.conclusions:
            ids.update(c.evidence_ids)
            for claim in c.numeric_claims:
                if claim.evidence_id:
                    ids.add(claim.evidence_id)
        return sorted(list(ids))


class AIProviderRequest(BaseModel):
    """
    Immutable request envelope dispatched to an AI provider.
    Carries only the M2 BoundedContext, prompt, and execution configuration.
    Zero access to database sessions, repositories, or cloud clients.
    """
    question: str
    system_prompt: str
    user_prompt: str
    bounded_context: Optional[BoundedContext] = None
    context_json: Optional[str] = None
    evidence_hash: str
    prompt_version: str = PROMPT_SYSTEM_VERSION
    context_version: str = CONTEXT_VERSION
    model: str = "gpt-4o-mini"
    request_id: str = ""
    temperature: float = 0.1
    max_tokens: int = 1500


class AIProviderResult(BaseModel):
    """
    Raw execution result returned by an AI provider invocation.
    Contains provider-reported token usage, latency, and untrusted candidate answer.
    """
    status: AIResponseStatus
    provider: str
    model: str
    candidate_answer: Optional[AICandidateAnswer] = None
    raw_response_text: Optional[str] = None
    raw_response_metadata: Dict[str, Any] = Field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: Decimal = Decimal("0.0000")
    latency_ms: int = 0
    request_id: str = ""
    evidence_hash: str = ""
    error_code: Optional[ProviderErrorCode] = None
    error_message: Optional[str] = None

    @field_validator("estimated_cost_usd", mode="before")
    @classmethod
    def _coerce_cost_decimal(cls, v: Any) -> Decimal:
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))
