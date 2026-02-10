"""
Domain models for financial transactions.

Includes Transaction and UpdateTransaction schemas with validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, computed_field
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
        account_type (str): Type of account the transaction is associated with
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
    account_type: Optional[str] = None
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
    def amount_not_zero(  # pylint: disable=no-self-argument
        cls,
        value: Decimal
    ) -> Decimal:
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

    @computed_field
    @property
    def direction(self) -> str:
        """
        Returns the flow of funds relative to the account.

        - "in" → money into the account (deposits, refunds, credit payments)
        - "out" → money leaving the account (purchases, withdrawals)
        
        Notes:
            For credit and loan accounts, the logic is inverted:
            an "incoming" transaction decreases balance, while "outgoing"
            increases it, so we flip the sign for display purposes.
        """
        is_incoming = self.category_primary in {"INCOME", "TRANSFER_IN"}

        if self.account_type in {"credit", "loan"}:
            is_incoming = not is_incoming

        return "in" if is_incoming else "out"
