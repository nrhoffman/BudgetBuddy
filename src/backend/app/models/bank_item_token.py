"""
SQLAlchemy ORM model for storing bank item tokens.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BankItemToken(Base):
    """
    ORM model representing a user's linked bank item token.

    Attributes:
        id: Primary key UUID for the record.
        user_id: Foreign key referencing the user.
        provider: Bank provider name (e.g., Plaid).
        access_token: Encrypted access token for the bank item.
        item_id: Optional bank item identifier.
        created_at: UTC timestamp when the token was created.
    """
    __tablename__ = "bank_item_tokens"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(nullable=False)

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    access_token: Mapped[str] = mapped_column(String, nullable=False)
    item_id: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
    )
