"""
NEXORA ATLAS - AI Interaction Domain Model (Phase 9)
Stores audit and provenance records for AI explanations.
Captures evidence references, canonical evidence hashes, token usage,
costs, and structured answers without duplicating raw analytical datastores.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, ForeignKey, Index, JSON, Numeric, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class AIInteraction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Auditable record of a natural language explanation query and response.
    Preserves provenance, evidence hash, and token usage.
    """
    __tablename__ = "ai_interactions"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    question: Mapped[str] = mapped_column(String(2000), nullable=False)
    question_category: Mapped[str] = mapped_column(String(50), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(50), nullable=False, default="DASHBOARD")
    scope_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="mock")
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="gpt-4o-mini")
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    context_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Context integrity hash: SHA-256 of canonicalized EvidencePackage JSON
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # Auditable list of evidence IDs cited or referenced
    evidence_ids: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    response_status: Mapped[str] = mapped_column(String(50), nullable=False)
    answer_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    # Bounded sanitized snapshot (capped at MAX_PERSISTED_EVIDENCE_BYTES)
    sanitized_evidence_preview: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False, default=Decimal("0.0"))
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    __table_args__ = (
        Index("idx_ai_interaction_org_created", "organization_id", "created_at"),
        Index("idx_ai_interaction_session_created", "session_id", "created_at"),
    )
