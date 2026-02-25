"""
Domain models for accounts.

Includes account types, subtypes, and conversion utilities for account data.
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any

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
    MONEY_MARKET = "money market"
    CASH_MANAGEMENT = "cash management"
    PREPAID = "prepaid"
    CD = "cd"
    EBT = "ebt"
    HEALTH_SAVINGS = "hsa"
    CREDIT_CARD = "credit card"
    AUTO_LOAN = "auto"
    STUDENT_LOAN = "student"
    MORTGAGE = "mortgage"
    LINE_OF_CREDIT = "line of credit"
    HOME_EQUITY = "home equity"
    OVERDRAFT = "overdraft"
    IRA = "ira"
    SEP_IRA = "sep ira"
    ROTH_IRA = "roth ira"
    SIMPLE_IRA = "simple ira"
    _401K = "401k"
    _403B = "403b"
    _457B = "457b"
    _529 = "529"
    OTHER = "other"


class UpdateAccount(BaseModel):
    """
    Schema for updating Account Name and APR.

    Attributes:
        account_name (Optional[str]): Account Name
        apr (Optional[Decimal]): APR/Interest of the account
    """

    account_name: Optional[str] = None
    apr: Optional[Decimal] = None


class Account(BaseModel):
    """
    Account domain model.

    Defines the core Account entity used throughout the banking domain layer.
    This model represents a financial account linked through an external
    banking provider and persisted within the application.

    The Account model encapsulates:

    - Core identity information (id, name, type, subtype)
    - Balance and credit details
    - Currency metadata
    - Interest rate information (APR)
    - System-level tracking fields for import state
    - Associated transaction records

    This model is intentionally provider-agnostic and serves as the canonical
    representation of an account within the application domain.
    """
    id: str
    name: str
    type: AccountType
    subtype: Optional[AccountSubType]
    logo: Optional[str] = None
    institution_id: Optional[str] = None

    # Balances
    balance: Decimal
    available_balance: Optional[Decimal] = None
    credit_limit: Optional[Decimal] = None

    # Currency
    iso_currency_code: Optional[str] = None
    unofficial_currency_code: Optional[str] = None

    # Metadata
    holder_category: Optional[str] = None
    apr: Optional[Decimal] = None

    # System
    initial_balance: Optional[Decimal] = None
    initial_import_completed_at: Optional[datetime] = None

    transactions: list[Transaction] = Field(default_factory=list)

    is_deleted: Optional[bool] = None
    deleted_at: Optional[datetime] = None


def parse_account_type(value: Any) -> AccountType:
    """
    Convert a value to an AccountType enum.

    Args:
        value (Any): The raw input value.

    Returns:
        AccountType: A valid AccountType enum; defaults to OTHER if invalid.
    """
    try:
        return AccountType(str(value).strip().lower())
    except ValueError:
        logger.debug("Unknown account type encountered: %s", value)
        return AccountType.OTHER


def parse_account_subtype(value: Any) -> AccountSubType:
    """
    Convert a value to an AccountSubType enum.

    Args:
        value (Any): The raw input value.

    Returns:
        AccountSubType: A valid AccountSubType enum; defaults to OTHER if invalid.
    """
    try:
        return AccountSubType(str(value).strip().lower())
    except ValueError:
        logger.debug("Unknown account subtype encountered: %s", value)
        return AccountSubType.OTHER
