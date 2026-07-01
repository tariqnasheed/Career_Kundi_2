"""
db/models/mixins.py
=======================
Reusable declarative mixins shared across ORM models to avoid repeating the
same boilerplate columns (UUID primary key, created/updated timestamps) in
every single model file.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column, generated client-side via uuid4."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    """Adds `created_at` / `updated_at` columns, both managed server-side."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class OrderableMixin:
    """Adds an `order_index` column for drag-and-drop reorderable list entries."""

    order_index: Mapped[int] = mapped_column(default=0, nullable=False)
