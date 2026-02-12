"""
SQLAlchemy ORM model for financial transactions.

Defines the TransactionORM table with fields for account linkage,
amounts, timestamps, merchant information, categories, and currencies.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TransactionORM(Base):
    """
    ORM model representing a financial transaction.

    Stores transaction amounts, category metadata, and links
    each transaction to its associated account.
    """

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
    )

    account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.id"),
    )

    account_type: Mapped[str] = mapped_column(String, nullable=False)

    account = relationship(
        "AccountORM",
        back_populates="transactions",
    )

    amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
    )

    date: Mapped[datetime] = mapped_column(
        default=datetime.now(timezone.utc),
    )

    balance_after: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    name: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    merchant_name: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    category_primary: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    category_detailed: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    category_confidence_level: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    pending: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    iso_currency_code: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    unofficial_currency_code: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

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
