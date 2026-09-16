"""
NEXORA ATLAS - Cloud Resource & Tag Models
Represents discovered asset inventory identity and configurations.
Operational telemetry (CPU/Memory) is explicitly decoupled from this model.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import String, ForeignKey, Index, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class CloudResource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Discovered cloud infrastructure asset."""
    __tablename__ = "cloud_resources"

    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cloud_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    region_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("cloud_regions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_arn: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    native_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    specs_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    account: Mapped["CloudAccount"] = relationship("CloudAccount", back_populates="resources")
    region: Mapped[Optional["CloudRegion"]] = relationship("CloudRegion", back_populates="resources")
    tags: Mapped[List["Tag"]] = relationship(
        "Tag", back_populates="resource", cascade="all, delete-orphan"
    )
    cost_records: Mapped[List["CostRecord"]] = relationship(
        "CostRecord", back_populates="resource"
    )
    optimization_opportunities: Mapped[List["OptimizationOpportunity"]] = relationship(
        "OptimizationOpportunity", back_populates="resource", cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="resource"
    )
    scenario_changes: Mapped[List["ScenarioChange"]] = relationship(
        "ScenarioChange", back_populates="resource"
    )

    __table_args__ = (
        UniqueConstraint("account_id", "native_id", name="uq_resource_account_native_id"),
        Index("ix_resources_account_service_type", "account_id", "service_name", "resource_type"),
    )


class Tag(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Resource metadata tag (Key-Value pair)."""
    __tablename__ = "tags"

    resource_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cloud_resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Relationships
    resource: Mapped["CloudResource"] = relationship("CloudResource", back_populates="tags")

    __table_args__ = (
        UniqueConstraint("resource_id", "key", name="uq_resource_tag_key"),
        Index("ix_tags_key_value", "key", "value"),
    )
