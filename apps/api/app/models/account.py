"""
NEXORA ATLAS - Cloud Account, Region, Integration & Sync Models
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class CloudRegion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Geographic regions across cloud providers."""
    __tablename__ = "cloud_regions"

    provider_type: Mapped[str] = mapped_column(String(50), default="AWS", nullable=False)
    region_code: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    resources: Mapped[List["CloudResource"]] = relationship("CloudResource", back_populates="region")

    __table_args__ = (
        UniqueConstraint("provider_type", "region_code", name="uq_region_provider_code"),
    )


class CloudAccount(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Connected cloud infrastructure account (e.g. AWS 12-digit Account)."""
    __tablename__ = "cloud_accounts"

    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_type: Mapped[str] = mapped_column(String(50), default="AWS", nullable=False)
    account_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="cloud_accounts")
    resources: Mapped[List["CloudResource"]] = relationship(
        "CloudResource", back_populates="account", cascade="all, delete-orphan"
    )
    cost_records: Mapped[List["CostRecord"]] = relationship(
        "CostRecord", back_populates="account", cascade="all, delete-orphan"
    )
    cost_snapshots: Mapped[List["CostSnapshot"]] = relationship(
        "CostSnapshot", back_populates="account", cascade="all, delete-orphan"
    )
    anomalies: Mapped[List["Anomaly"]] = relationship(
        "Anomaly", back_populates="account", cascade="all, delete-orphan"
    )
    optimization_opportunities: Mapped[List["OptimizationOpportunity"]] = relationship(
        "OptimizationOpportunity", back_populates="account", cascade="all, delete-orphan"
    )
    forecasts: Mapped[List["Forecast"]] = relationship(
        "Forecast", back_populates="account", cascade="all, delete-orphan"
    )
    sync_jobs: Mapped[List["SyncJob"]] = relationship(
        "SyncJob", back_populates="account"
    )

    __table_args__ = (
        UniqueConstraint("org_id", "provider_type", "account_id", name="uq_account_org_provider_account_id"),
        Index("ix_cloud_accounts_org_status", "org_id", "status"),
    )


class Integration(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Provider connection configuration and credential metadata."""
    __tablename__ = "integrations"

    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_type: Mapped[str] = mapped_column(String(50), default="AWS", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    auth_method: Mapped[str] = mapped_column(String(50), default="IAM_ROLE", nullable=False)
    config_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="integrations")
    sync_jobs: Mapped[List["SyncJob"]] = relationship(
        "SyncJob", back_populates="integration", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_integrations_org_provider", "org_id", "provider_type"),
    )


class SyncJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Ingestion synchronization run record (completely offline in Phase 1 & 2)."""
    __tablename__ = "sync_jobs"

    integration_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("cloud_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    job_type: Mapped[str] = mapped_column(String(50), default="COST_SYNC", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    records_synced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationships
    integration: Mapped["Integration"] = relationship("Integration", back_populates="sync_jobs")
    account: Mapped[Optional["CloudAccount"]] = relationship("CloudAccount", back_populates="sync_jobs")

    __table_args__ = (
        Index("ix_sync_jobs_status_started", "status", "started_at"),
    )
