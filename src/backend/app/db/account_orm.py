"""
SQLAlchemy ORM model for user accounts.

Defines the AccountORM table with relationships to transactions and
user ownership.
"""

from sqlalchemy import String, Enum, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.account import AccountType, AccountSubType


class AccountORM(Base):
    """ORM model representing a user account."""

    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]
    type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, name="account_type")
    )
    subtype: Mapped[AccountSubType | None] = mapped_column(
        Enum(AccountSubType, name="account_subtype"), nullable=True
    )
    balance: Mapped[float] = mapped_column(Numeric(12, 2))

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    transactions = relationship(
        "TransactionORM",
        back_populates="account",
        cascade="all, delete-orphan",
    )
