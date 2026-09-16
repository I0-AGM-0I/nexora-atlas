"""
NEXORA ATLAS - Financial Cost Telemetry Models
Represents granular cost records and period snapshots.
Uses precise Numeric(18, 4) to eliminate floating point rounding errors.
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import date
from sqlalchemy import String, Date, Numeric, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class CostRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Granular financial line item derived from cloud billing."""
    __tablename__ = "cost_records"

    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cloud_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("cloud_resources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    service_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    usage_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    unblended_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    amortized_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    usage_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    usage_unit: Mapped[str] = mapped_column(String(50), default="Hrs", nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)

    # Relationships
    account: Mapped["CloudAccount"] = relationship("CloudAccount", back_populates="cost_records")
    resource: Mapped[Optional["CloudResource"]] = relationship("CloudResource", back_populates="cost_records")

    __table_args__ = (
        Index("ix_cost_records_account_date_service", "account_id", "usage_date", "service_name"),
        Index("ix_cost_records_resource_date", "resource_id", "usage_date"),
    )


class CostSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Pre-computed cost rollups for high-velocity dashboard & time-series queries."""
    __tablename__ = "cost_snapshots"

    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cloud_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), default="MONTHLY", nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    breakdown_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    account: Mapped["CloudAccount"] = relationship("CloudAccount", back_populates="cost_snapshots")

    __table_args__ = (
        Index("ix_cost_snapshots_account_period", "account_id", "period_start", "period_type"),
    )
