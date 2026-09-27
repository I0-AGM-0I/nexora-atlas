"""
NEXORA ATLAS - Operational Telemetry Domain Model
Stores raw source-level metric observations retrieved from cloud providers.
Derived analytical metrics (p95, median, CV) are calculated at the analytics
layer and never stored as raw source statistics.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, ForeignKey, Index, UniqueConstraint, JSON, Numeric, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class ResourceMetricObservation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Canonical operational telemetry data point.
    Decoupled from inventory and financial models.
    """
    __tablename__ = "resource_metric_observations"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cloud_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cloud_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cloud_resources.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Deterministic SHA-256 deduplication key:
    # sha256(provider | account | region | namespace | metric_name | dimensions_sorted | timestamp_iso | period | source_statistic)
    source_observation_key: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )

    provider_type: Mapped[str] = mapped_column(String(50), default="AWS", nullable=False)
    metric_namespace: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Source statistic as published/requested from AWS (Average, Maximum, Sum, etc.)
    # Never store Atlas derived p95 here.
    source_statistic: Mapped[str] = mapped_column(String(50), nullable=False)

    period_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="Percent", nullable=False)

    dimensions_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="cloudwatch", nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    sync_job_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sync_jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    resource: Mapped["CloudResource"] = relationship("CloudResource", backref="metric_observations")
    account: Mapped["CloudAccount"] = relationship("CloudAccount")
    organization: Mapped["Organization"] = relationship("Organization")
    sync_job: Mapped[Optional["SyncJob"]] = relationship("SyncJob")

    __table_args__ = (
        UniqueConstraint("source_observation_key", name="uq_telemetry_source_observation_key"),
        Index("ix_telemetry_resource_metric_ts", "resource_id", "metric_name", "timestamp"),
        Index("ix_telemetry_account_metric_ts", "cloud_account_id", "metric_name", "timestamp"),
    )
