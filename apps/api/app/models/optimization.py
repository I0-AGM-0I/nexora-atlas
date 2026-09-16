"""
NEXORA ATLAS - Optimization Opportunity & Recommendation Models
Separates detected inefficiency (Opportunity) from proposed action (Recommendation).
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Numeric, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class OptimizationOpportunity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Detected hardware or storage inefficiency / waste."""
    __tablename__ = "optimization_opportunities"

    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cloud_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("cloud_resources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    waste_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)
    estimated_waste_monthly: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    evidence_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    account: Mapped["CloudAccount"] = relationship("CloudAccount", back_populates="optimization_opportunities")
    resource: Mapped[Optional["CloudResource"]] = relationship("CloudResource", back_populates="optimization_opportunities")
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="opportunity", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_opportunities_account_status", "account_id", "status"),
    )


class Recommendation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Actionable right-sizing, tiering, or termination blueprint."""
    __tablename__ = "recommendations"

    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("optimization_opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("cloud_resources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    current_configuration: Mapped[str] = mapped_column(String(500), nullable=False)
    recommended_configuration: Mapped[str] = mapped_column(String(500), nullable=False)
    estimated_monthly_savings: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    estimated_annual_savings: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    confidence_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW", nullable=False)
    reasoning: Mapped[str] = mapped_column(String(1000), nullable=False)
    evidence_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)

    # Relationships
    opportunity: Mapped["OptimizationOpportunity"] = relationship("OptimizationOpportunity", back_populates="recommendations")
    resource: Mapped[Optional["CloudResource"]] = relationship("CloudResource", back_populates="recommendations")

    __table_args__ = (
        Index("ix_recommendations_opp_status", "opportunity_id", "status"),
        Index("ix_recommendations_category_risk", "category", "risk_level"),
    )
