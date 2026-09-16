"""
NEXORA ATLAS - Declarative ORM Base Models
Provides portable primary keys and audit timestamps compatible with PostgreSQL and SQLite.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def generate_uuid() -> str:
    """Generate a standard UUID4 hex string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy entities."""
    pass


class TimestampMixin:
    """Standardized auditing timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """Portable UUID4 string primary key."""
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True,
    )
