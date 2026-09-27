"""
NEXORA ATLAS - AI Schemas (Phase 9)
Request and response models for the AI Explanation API endpoints.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.ai.types import ScopeType, AIResponseStatus, EpistemicClass
from app.ai.models import AIAnswer, DataFreshness


class AIAskRequest(BaseModel):
    """Payload for asking a natural language question in Atlas."""
    question: str = Field(..., min_length=2, max_length=2000, description="Natural language question")
    scope_type: ScopeType = Field(default=ScopeType.DASHBOARD, description="Scope boundary for analysis")
    scope_id: Optional[str] = Field(default=None, description="Target entity ID (resource, account, etc.)")
    session_id: Optional[str] = Field(default=None, description="Conversation session ID for conversational context")


class AIAskResponse(BaseModel):
    """Comprehensive, auditable explanation response returned to user."""
    interaction_id: str
    session_id: str
    status: AIResponseStatus
    question: str
    scope_type: ScopeType
    scope_id: Optional[str] = None
    answer: Optional[AIAnswer] = None
    evidence_hash: str
    evidence_count: int
    evidence_ids: List[str]
    data_freshness: DataFreshness
    latency_ms: int
    token_count: int
    estimated_cost_usd: Decimal
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime


class AIStatusResponse(BaseModel):
    """Subsystem health, feature flag, and model configuration."""
    ai_enabled: bool
    provider: str
    model: str
    max_context_tokens: int
    max_output_tokens: int
    rate_limit_per_minute: int
    system_version: str
    prompt_version: str
    is_offline_capable: bool


class AIInteractionDetailResponse(BaseModel):
    """Full audit record of a past AI explanation."""
    id: str
    organization_id: str
    session_id: str
    question: str
    question_category: str
    scope_type: str
    scope_id: Optional[str] = None
    provider: str
    model: str
    prompt_version: str
    context_version: str
    evidence_hash: str
    evidence_ids: List[str]
    response_status: str
    answer_json: Optional[Dict[str, Any]] = None
    sanitized_evidence_preview: Optional[Dict[str, Any]] = None
    latency_ms: int
    input_token_count: int
    output_token_count: int
    estimated_cost_usd: Decimal
    evidence_count: int
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
