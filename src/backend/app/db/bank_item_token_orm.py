"""
SQLAlchemy ORM model for storing bank item tokens.

Persists access tokens and metadata for third-party banking providers.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BankItemTokenORM(Base):
    """
    ORM model representing a bank item access token.

    Stores provider credentials and institution metadata
    associated with a user's bank item.
    """

    __tablename__ = "bank_item_tokens"

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str] = mapped_column(nullable=False)

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    institution_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    institution_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    access_token: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    item_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
    )
