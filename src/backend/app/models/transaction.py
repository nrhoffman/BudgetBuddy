"""
Domain models for financial transactions.

Includes Transaction and UpdateTransaction schemas with validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from app.logger import logger


class UpdateTransaction(BaseModel):
    """
    Schema for updating transaction categories.

    Attributes:
        category_primary (Optional[str]): Primary category.
        category_detailed (Optional[str]): Detailed category.
        category_confidence_level (Optional[str]): Confidence level, default 'MANUAL'.
    """

    category_primary: Optional[str] = None
    category_detailed: Optional[str] = None
    category_confidence_level: Optional[str] = "MANUAL"


class Transaction(BaseModel):
    """
    Domain model representing a financial transaction.

    Attributes:
        transaction_id (str): Unique transaction ID.
        account_id (str): ID of the associated account.
        amount (Decimal): Transaction amount; must not be zero.
        date (datetime): Transaction timestamp.
        balance_after (Optional[Decimal]): Account balance after transaction.
        name (Optional[str]): Transaction name.
        merchant_name (Optional[str]): Merchant name.
        category_primary (Optional[str]): Primary category.
        category_detailed (Optional[str]): Detailed category.
        category_confidence_level (Optional[str]): Confidence level.
        pending (Optional[bool]): True if transaction is pending.
        iso_currency_code (Optional[str]): ISO currency code.
        unofficial_currency_code (Optional[str]): Non-standard currency code.
    """

    transaction_id: str = Field(..., alias="id")
    account_id: str
    amount: Decimal
    date: datetime
    balance_after: Optional[Decimal] = None
    name: Optional[str] = None
    merchant_name: Optional[str] = None
    category_primary: Optional[str] = None
    category_detailed: Optional[str] = None
    category_confidence_level: Optional[str] = None
    pending: Optional[bool] = None
    iso_currency_code: Optional[str] = None
    unofficial_currency_code: Optional[str] = None

    model_config = {
        "populate_by_name": True
    }

    @field_validator("amount")
    def amount_not_zero(cls, value: Decimal) -> Decimal:  # pylint: disable=no-self-argument
        """
        Validate that the transaction amount is not zero.

        Args:
            value (Decimal): Transaction amount.

        Returns:
            Decimal: Validated transaction amount.

        Raises:
            ValueError: If amount is zero.
        """
        if value == 0:
            logger.debug("Validation failed: transaction amount cannot be zero")
            raise ValueError("Transaction amount cannot be zero")
        return value
