"""
SQLAlchemy ORM model for storing bank item cursors.

Tracks the last synchronization cursor for a given user and bank item.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BankItemCursor(Base):
    """
    ORM model representing a bank item cursor.

    Each record stores the latest cursor value for a specific
    user and bank item combination.
    """

    __tablename__ = "bank_item_cursors"

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str] = mapped_column(nullable=False)
    item_id: Mapped[str] = mapped_column(nullable=False)

    cursor: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
    )
