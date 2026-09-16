"""
NEXORA ATLAS - Organization & AuditLog Models
Defines multi-tenant boundaries and immutable governance audit trails.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, utc_now


class Organization(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    cloud_accounts: Mapped[List["CloudAccount"]] = relationship(
        "CloudAccount", back_populates="organization", cascade="all, delete-orphan"
    )
    integrations: Mapped[List["Integration"]] = relationship(
        "Integration", back_populates="organization", cascade="all, delete-orphan"
    )
    scenarios: Mapped[List["Scenario"]] = relationship(
        "Scenario", back_populates="organization", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="organization", cascade="all, delete-orphan"
    )


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """
    Append-only immutable audit trail recording security, ingestion, and operational actions.
    Note: Has no updated_at column to ensure immutable semantics.
    """
    __tablename__ = "audit_logs"

    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False, index=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_org_timestamp", "org_id", "timestamp"),
    )
