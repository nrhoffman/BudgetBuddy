"""
SQLAlchemy ORM model for user accounts.

Defines the AccountORM table with relationships to transactions and
user ownership.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.account import AccountSubType, AccountType


class AccountORM(Base):
    """
    ORM model representing a user account.

    Stores account metadata, balances, and relationships to
    transactions and the owning user.
    """

    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]

    type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, name="account_type")
    )

    subtype: Mapped[AccountSubType | None] = mapped_column(
        Enum(AccountSubType, name="account_subtype"),
        nullable=True,
    )

    logo: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )
    institution_id: Mapped[str] = mapped_column(String)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    available_balance: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    credit_limit: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    iso_currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    unofficial_currency_code: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
    )

    holder_category: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    initial_import_completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )

    apr: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    transactions = relationship(
        "TransactionORM",
        back_populates="account",
        cascade="all, delete-orphan",
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
