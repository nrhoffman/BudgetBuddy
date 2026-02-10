"""
SQLAlchemy ORM for raw provider events.

This module defines the RawProviderORM model, which stores immutable events
retrieved from external banking providers. Each event includes the raw payload,
user/item identity, incremental sync cursors, and timestamps for auditing and
future processing.
"""

from datetime import datetime
from uuid import uuid4
from typing import Optional

from sqlalchemy import String, DateTime, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RawProviderORM(Base):
    """
    ORM model representing a raw banking provider event.

    Attributes:
        id (UUID): Primary key for the raw event.
        provider (str): Name of the external provider (e.g., 'plaid').
        endpoint (str): API endpoint or action that produced this event.
        user_id (Optional[str]): ID of the user associated with the provider item.
        item_id (Optional[str]): Provider-specific item identifier for the linked
        institution.
        cursor_before (Optional[str]): Cursor value before the incremental sync.
        cursor_after (Optional[str]): Cursor value after the incremental sync.
        fetched_at (datetime): Timestamp when the event was stored in the database.
        payload (dict): Raw JSON payload returned by the provider.
    """

    __tablename__ = "raw_provider_events"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "endpoint",
            "item_id",
            "cursor_after",
            name="uq_raw_provider_event_cursor"
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Primary key UUID for the raw event."
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Name of the external provider (e.g., 'plaid')."
    )

    endpoint: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="API endpoint or action that produced this event."
    )

    user_id: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        index=True,
        doc="ID of the user associated with the provider item."
    )

    item_id: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        index=True,
        doc="Provider-specific item ID for the linked institution."
    )

    cursor_before: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        doc="Cursor value before the incremental sync."
    )

    cursor_after: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        doc="Cursor value after the incremental sync."
    )

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
        nullable=False,
        doc="Timestamp when the event was stored in the database."
    )

    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        doc="Raw JSON payload returned by the provider."
    )
