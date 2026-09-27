"""
NEXORA ATLAS - AI Domain Contracts & Models (Phase 9)
Structured Pydantic models for evidence representation, verification claims,
and AI explanation outputs.
"""

from typing import Optional, Dict, Any, List, Set
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from app.ai.types import (
    EpistemicClass,
    ScopeType,
    QuestionCategory,
    AIResponseStatus,
    ProviderErrorCode,
    DataFreshnessStatus,
)


def _check_no_confidence_recursive(data: Any, path: str = "root") -> None:
    """
    Recursively inspects data structures and rejects any field named 'confidence'.
    Preserves enterprise invariant: AI must never generate confidence scores.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if k == "confidence":
                raise ValueError(
                    f"AI-generated confidence score detected at '{path}.confidence'; prohibited by Atlas contract."
                )
            _check_no_confidence_recursive(v, f"{path}.{k}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            _check_no_confidence_recursive(item, f"{path}[{i}]")


class NumericClaim(BaseModel):
    """
    Structured numeric claim output by the AI model.
    Enforces Decimal precision for financial quantities to avoid binary floating-point inaccuracies.
    """
    value: Decimal
    unit: str
    evidence_ids: List[str] = Field(default_factory=list)
    evidence_id: Optional[str] = None
    description: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_claim_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Coerce value to Decimal via string representation to avoid float inaccuracies
            val = data.get("value")
            if val is not None and not isinstance(val, Decimal):
                data["value"] = Decimal(str(val))

            # Harmonize evidence_id and evidence_ids
            eid = data.get("evidence_id")
            eids = data.get("evidence_ids")
            if eid and not eids:
                data["evidence_ids"] = [eid]
            elif eids and not eid:
                data["evidence_id"] = eids[0] if len(eids) > 0 else None
        return data

    @property
    def primary_evidence_id(self) -> Optional[str]:
        """Returns the primary evidence ID cited by this claim."""
        if self.evidence_ids:
            return self.evidence_ids[0]
        return self.evidence_id


class EvidenceItem(BaseModel):
    """
    Individual atomic evidence item produced by deterministic Atlas engines.
    Immutable (frozen=True) to guarantee deterministic provenance.
    """
    model_config = ConfigDict(frozen=True)

    id: str
    type: str  # e.g., SPEND_TOTAL, DRIVER, METRIC_P95, RECOMMENDATION, ANOMALY, SCENARIO
    epistemic_class: EpistemicClass
    statement: str
    value: Optional[Decimal] = None
    unit: Optional[str] = None
    source: str = "Atlas Analytics Engine"  # e.g. "Cost Explorer", "CloudWatch", "Atlas Analytics Engine", "Atlas Optimizer"
    source_entity_id: Optional[str] = None
    confidence: Optional[float] = None  # Authoritative from Atlas only; AI-generated confidence is prohibited
    period_or_timestamp: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("value", mode="before")
    @classmethod
    def _coerce_decimal(cls, v: Any) -> Optional[Decimal]:
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class DataFreshness(BaseModel):
    """
    Tracks observation timestamps and data age to prevent implying real-time knowledge.
    """
    cloudwatch_retrieved_at: Optional[datetime] = None
    cost_data_through: Optional[str] = None
    resource_inventory_synced_at: Optional[datetime] = None
    status: DataFreshnessStatus = DataFreshnessStatus.UNKNOWN
    freshness_summary: str = "Data freshness information not yet loaded."


class EvidencePackage(BaseModel):
    """
    Normalized, sanitized, and budgeted evidence package passed into the AI explanation engine.
    """
    scope_type: ScopeType
    scope_id: Optional[str] = None
    freshness: DataFreshness = Field(default_factory=DataFreshness)
    observations: List[EvidenceItem] = Field(default_factory=list)
    derived_metrics: List[EvidenceItem] = Field(default_factory=list)
    inferences: List[EvidenceItem] = Field(default_factory=list)
    recommendations: List[EvidenceItem] = Field(default_factory=list)
    scenarios: List[EvidenceItem] = Field(default_factory=list)
    telemetry: List[EvidenceItem] = Field(default_factory=list)
    data_quality: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    is_context_limited: bool = False
    evidence_count: int = 0

    def all_items(self) -> List[EvidenceItem]:
        """Returns all evidence items across all categories."""
        return (
            self.observations
            + self.derived_metrics
            + self.inferences
            + self.recommendations
            + self.scenarios
            + self.telemetry
        )

    def get_item(self, evidence_id: str) -> Optional[EvidenceItem]:
        """Looks up an evidence item by its unique ID."""
        for item in self.all_items():
            if item.id == evidence_id:
                return item
        return None

    def get_numeric_item(self, evidence_id: str) -> Optional[EvidenceItem]:
        """Looks up an evidence item with a non-null numerical value."""
        item = self.get_item(evidence_id)
        if item and item.value is not None:
            return item
        return None

    def cited_evidence_ids(self) -> List[str]:
        """Returns ordered list of all evidence IDs present in this package."""
        return [item.id for item in self.all_items()]

    def canonical_json(self) -> str:
        """Serializes package to canonical deterministically-sorted JSON string."""
        from app.ai.context.hasher import canonicalize_evidence_package
        return canonicalize_evidence_package(self)

    def compute_hash(self) -> str:
        """Computes deterministic SHA-256 evidence package hash."""
        from app.ai.context.hasher import compute_evidence_hash
        return compute_evidence_hash(self)


class AICitation(BaseModel):
    """
    Clickable citation linking natural language statements to Atlas domain entities.
    """
    id: str
    title: str
    entity_type: str  # RESOURCE, RECOMMENDATION, COST, ANOMALY, SCENARIO
    entity_id: str
    link_path: str
    description: Optional[str] = None


class AIConclusion(BaseModel):
    """
    Atomic conclusion derived directly from cited evidence.
    AI-generated confidence scores are strictly prohibited.
    """
    statement: str
    epistemic_class: EpistemicClass
    evidence_ids: List[str] = Field(default_factory=list)
    numeric_claims: List[NumericClaim] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _reject_confidence(cls, data: Any) -> Any:
        _check_no_confidence_recursive(data, "conclusion")
        return data


class AIAnswer(BaseModel):
    """
    Structured, fully validated explanation returned to the user interface.
    """
    summary: str
    answer: str
    conclusions: List[AIConclusion] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    cited_entities: List[AICitation] = Field(default_factory=list)
    epistemic_notes: List[str] = Field(default_factory=list)
    freshness_note: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _reject_confidence(cls, data: Any) -> Any:
        _check_no_confidence_recursive(data, "answer")
        return data


class AIResponse(BaseModel):
    """
    Execution envelope for AI subsystem operations.
    """
    status: AIResponseStatus
    answer: Optional[AIAnswer] = None
    raw_text: Optional[str] = None
    error_code: Optional[ProviderErrorCode] = None
    error_message: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    estimated_cost_usd: Decimal = Decimal("0.0")


class AIQuestion(BaseModel):
    """
    Deterministic internal representation of an authorized user inquiry.
    Classification router populates 'category', but authorization fields
    must be verified against tenant context.
    """
    question: str
    category: Optional[QuestionCategory] = None
    scope_type: ScopeType = ScopeType.DASHBOARD
    organization_id: str
    account_id: Optional[str] = None
    service_name: Optional[str] = None
    resource_id: Optional[str] = None
    recommendation_id: Optional[str] = None
    scenario_id: Optional[str] = None


class BoundedContext(BaseModel):
    """
    Bounded, sanitized, and canonicalized context envelope produced by ContextBuilder.
    Ready for cryptographic provenance and future AI provider input.
    """
    evidence_items: List[EvidenceItem]
    included_count: int
    excluded_count: int
    is_context_limited: bool
    freshness_status: DataFreshnessStatus
    limitations: List[str] = Field(default_factory=list)
    canonical_json: str
    sha256_hash: str

