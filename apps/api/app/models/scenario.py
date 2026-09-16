"""
NEXORA ATLAS - Scenario Simulation Models
Represents hypothetical architecture optimization states and discrete infrastructure alterations.
Pure simulation - zero cloud execution.
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Numeric, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Scenario(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Simulated infrastructure optimization state."""
    __tablename__ = "scenarios"

    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    baseline_monthly_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    projected_monthly_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    monthly_savings: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    percentage_savings: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)

    performance_risk: Mapped[str] = mapped_column(String(20), default="LOW", nullable=False)
    reliability_risk: Mapped[str] = mapped_column(String(20), default="LOW", nullable=False)
    complexity_level: Mapped[str] = mapped_column(String(20), default="LOW", nullable=False)
    assumptions_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="scenarios")
    changes: Mapped[List["ScenarioChange"]] = relationship(
        "ScenarioChange", back_populates="scenario", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_scenarios_org_created", "org_id", "created_at"),
    )


class ScenarioChange(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Discrete simulated infrastructure change within a scenario."""
    __tablename__ = "scenario_changes"

    scenario_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("cloud_resources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    current_spec: Mapped[str] = mapped_column(String(500), nullable=False)
    proposed_spec: Mapped[str] = mapped_column(String(500), nullable=False)
    delta_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    # Relationships
    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="changes")
    resource: Mapped[Optional["CloudResource"]] = relationship("CloudResource", back_populates="scenario_changes")

    __table_args__ = (
        Index("ix_scenario_changes_scenario_resource", "scenario_id", "resource_id"),
    )
