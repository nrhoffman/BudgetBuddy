"""
SQLAlchemy ORM model for financial transactions.

Defines the TransactionORM table with fields for account linkage,
amounts, timestamps, merchant information, categories, and currencies.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Numeric,
    String,
    DateTime,
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TransactionORM(Base):
    """
    ORM model representing a financial transaction.

    Stores transaction amounts, category metadata, and links
    each transaction to its associated account.
    """

    __tablename__ = "transactions"

 # --------------------
    # Core Identifiers
    # --------------------
    id: Mapped[str] = mapped_column(String, primary_key=True)

    account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )

    account_type: Mapped[str | None] = mapped_column(String, nullable=True)

    account = relationship(
        "AccountORM",
        back_populates="transactions",
    )

    # --------------------
    # Monetary Data
    # --------------------
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    balance_after: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    iso_currency_code: Mapped[str | None] = mapped_column(String, nullable=True)
    unofficial_currency_code: Mapped[str | None] = mapped_column(String, nullable=True)

    # --------------------
    # Dates
    # --------------------
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    authorized_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    authorized_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # --------------------
    # Merchant Metadata
    # --------------------
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    merchant_name: Mapped[str | None] = mapped_column(String, nullable=True)
    merchant_entity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    merchant_website: Mapped[str | None] = mapped_column(String, nullable=True)
    merchant_logo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    merchant_confidence_level: Mapped[str | None] = mapped_column(String, nullable=True)

    # --------------------
    # Categorization
    # --------------------
    category_primary: Mapped[str | None] = mapped_column(String, nullable=True)
    category_detailed: Mapped[str | None] = mapped_column(String, nullable=True)
    category_confidence_level: Mapped[str | None] = mapped_column(String, nullable=True)
    plaid_category_version: Mapped[str | None] = mapped_column(String, nullable=True)

    # --------------------
    # Payment Metadata
    # --------------------
    payment_channel: Mapped[str | None] = mapped_column(String, nullable=True)
    transaction_type: Mapped[str | None] = mapped_column(String, nullable=True)
    transaction_code: Mapped[str | None] = mapped_column(String, nullable=True)

    # --------------------
    # Location Data
    # --------------------
    location_city: Mapped[str | None] = mapped_column(String, nullable=True)
    location_region: Mapped[str | None] = mapped_column(String, nullable=True)
    location_country: Mapped[str | None] = mapped_column(String, nullable=True)
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    store_number: Mapped[str | None] = mapped_column(String, nullable=True)

    # --------------------
    # Derived System Flags
    # --------------------
    is_ach: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_transfer: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_internal_transfer: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_recurring: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    pending: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    @property
    def direction(self) -> str:
        """
        Determine cash flow direction relative to the user.

        Returns:
            str: "in" if money is received by the user,
                "out" if money leaves the user.

        Rules:
            Depository / checking/savings:
                INCOME, TRANSFER_IN  -> "in"
                EXPENSE, TRANSFER_OUT -> "out"
            Credit/Loan:
                INCOME, TRANSFER_IN  -> "out"  (payment reduces balance owed)
                EXPENSE, TRANSFER_OUT -> "in"  (charges increase balance owed)
        """

        if self.account_type in {"credit", "loan"}:
            if self.category_primary in {"TRANSFER_OUT"}:
                return "out"
            return "in"
        if self.category_primary in {"INCOME", "TRANSFER_IN"}:
            return "in"
        return "out"
