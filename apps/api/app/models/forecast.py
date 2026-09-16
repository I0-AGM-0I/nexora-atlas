"""
NEXORA ATLAS - Forecast Model
Represents forward-looking statistical spending projections and bounds.
"""

from decimal import Decimal
from typing import Dict, Any, List
from datetime import date
from sqlalchemy import String, Date, Numeric, ForeignKey, Index, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Forecast(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Projected future technology expenditure with confidence bounds."""
    __tablename__ = "forecasts"

    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cloud_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    forecast_month: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    projected_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    lower_bound: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    upper_bound: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    confidence_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("85.00"), nullable=False)
    cost_drivers_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(50), default="STATISTICAL_TREND", nullable=False)

    # Relationships
    account: Mapped["CloudAccount"] = relationship("CloudAccount", back_populates="forecasts")

    __table_args__ = (
        UniqueConstraint("account_id", "forecast_month", name="uq_forecast_account_month"),
        Index("ix_forecasts_account_month", "account_id", "forecast_month"),
    )
