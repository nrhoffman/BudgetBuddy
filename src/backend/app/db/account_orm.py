"""
SQLAlchemy ORM model for user accounts.

Defines the AccountORM table with relationships to transactions and
user ownership.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
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

    balance: Mapped[float] = mapped_column(Numeric(12, 2))

    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    initial_import_completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    transactions = relationship(
        "TransactionORM",
        back_populates="account",
        cascade="all, delete-orphan",
    )
