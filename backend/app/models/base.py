"""
Base model mixin for all SQLAlchemy ORM models.

Provides shared columns: UUID primary key, audit timestamps,
and soft-delete support. All domain models inherit from this.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    Adds created_at and updated_at timestamp columns.

    Timestamps are stored as timezone-aware UTC datetimes.
    updated_at is automatically refreshed on every row update.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp when the record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="UTC timestamp of the most recent update",
    )


class SoftDeleteMixin:
    """
    Adds soft-delete support: records are flagged rather than physically removed.

    Services must filter is_deleted=False in all non-admin queries.
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        index=True,
        doc="When True, the record is considered deleted (soft delete)",
    )


class UUIDPrimaryKeyMixin:
    """
    Replaces integer IDs with UUID v4 primary keys.

    UUIDs prevent enumeration attacks and simplify distributed ID generation.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Universally unique identifier for this record",
    )
