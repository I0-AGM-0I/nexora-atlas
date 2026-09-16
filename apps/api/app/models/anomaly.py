"""
NEXORA ATLAS - Anomaly Detection Model
Maintains strict structural separation between Observed Data (facts) and Inferences (hypotheses).
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Anomaly(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Detected spending anomaly.
    Explicitly separates empirical observed facts from algorithmic inferences.
    """
    __tablename__ = "anomalies"

    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cloud_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("cloud_resources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    service_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # --- OBSERVED FACTS ---
    observed_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    baseline_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    percentage_change: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    detection_rule: Mapped[str] = mapped_column(String(100), nullable=False)
    observed_metrics_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # --- INFERRED ANALYSIS ---
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)
    inferred_cause: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    confidence_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("90.00"), nullable=False)
    inference_details_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    account: Mapped["CloudAccount"] = relationship("CloudAccount", back_populates="anomalies")
    resource: Mapped[Optional["CloudResource"]] = relationship("CloudResource")

    __table_args__ = (
        Index("ix_anomalies_account_severity_status", "account_id", "severity", "status"),
        Index("ix_anomalies_account_detected", "account_id", "detected_at"),
    )
