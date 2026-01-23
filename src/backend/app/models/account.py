"""
Domain models for accounts.

Includes types, subtypes, and conversion utilities for account data.
"""

import enum
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field
from app.logger import logger
from app.models.transaction import Transaction


class AccountType(str, enum.Enum):
    """Enumeration of account types."""
    DEPOSITORY = "depository"
    CREDIT = "credit"
    BROKERAGE = "brokerage"
    INVESTMENT = "investment"
    LOAN = "loan"
    OTHER = "other"


class AccountSubType(str, enum.Enum):
    """Enumeration of account subtypes."""
    CHECKING = "checking"
    SAVINGS = "savings"
    AUTO = "auto"
    STUDENT = "student"
    MORTGAGE = "mortgage"
    HOMEEQUITY = "home equity"
    LINEOFCREDIT = "line of credit"
    HSA = "hsa"
    OTHER = "other"


class Account(BaseModel):
    """Domain model for a bank account."""
    id: str
    name: str
    type: AccountType
    subtype: Optional[AccountSubType]
    balance: Decimal
    transactions: List[Transaction] = Field(default_factory=list)


def parse_account_type(value) -> AccountType:
    """
    Convert a value to an AccountType enum.

    Args:
        value: The raw input value.

    Returns:
        AccountType: A valid AccountType enum; defaults to OTHER if invalid.
    """
    try:
        return AccountType(str(value).strip().lower())
    except ValueError:
        logger.debug(f"Unknown account type encountered: {value}")
        return AccountType.OTHER


def parse_account_subtype(value) -> AccountSubType:
    """
    Convert a value to an AccountSubType enum.

    Args:
        value: The raw input value.

    Returns:
        AccountSubType: A valid AccountSubType enum; defaults to OTHER if invalid.
    """
    try:
        return AccountSubType(str(value).strip().lower())
    except ValueError:
        logger.debug(f"Unknown account subtype encountered: {value}")
        return AccountSubType.OTHER
