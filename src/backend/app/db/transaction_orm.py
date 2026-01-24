"""
SQLAlchemy ORM model for financial transactions.

Defines the TransactionORM table with fields for account linkage, amounts,
timestamps, merchant info, categories, and currency codes.
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, String, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TransactionORM(Base):
    """ORM model representing a financial transaction."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    account = relationship("AccountORM", back_populates="transactions")

    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    date: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))

    name: Mapped[str | None] = mapped_column(String, nullable=True)
    merchant_name: Mapped[str | None] = mapped_column(String, nullable=True)
    category_primary: Mapped[str | None] = mapped_column(String, nullable=True)
    category_detailed: Mapped[str | None] = mapped_column(String, nullable=True)
    category_confidence_level: Mapped[str | None] = mapped_column(String, nullable=True)

    pending: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    iso_currency_code: Mapped[str | None] = mapped_column(String, nullable=True)
    unofficial_currency_code: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )
