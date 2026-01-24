"""
Pydantic model for representing a financial transaction.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.logger import logger


class Transaction(BaseModel):
    """
    Represents a financial transaction.

    Attributes:
        transaction_id: Unique identifier for the transaction.
        account_id: ID of the account associated with this transaction.
        amount: Transaction amount (cannot be zero).
        date: Date and time of the transaction.
        name: Optional transaction name.
        merchant_name: Optional merchant name.
        category: Optional list of transaction categories.
        pending: Optional boolean indicating if the transaction is pending.
        iso_currency_code: Optional ISO currency code.
        unofficial_currency_code: Optional unofficial currency code.
    """
    transaction_id: str = Field(..., alias="id")
    account_id: str
    amount: Decimal
    date: datetime
    name: Optional[str] = None
    merchant_name: Optional[str] = None
    category: Optional[List[str]] = None
    pending: Optional[bool] = None
    iso_currency_code: Optional[str] = None
    unofficial_currency_code: Optional[str] = None

    model_config = {
        "populate_by_name": True
    }

    @field_validator("amount") # pylint: disable=no-self-argument
    def amount_not_zero(cls, v: Decimal) -> Decimal:
        """
        Ensure the transaction amount is not zero.
        """
        if v == 0:
            logger.debug("Validation failed: transaction amount cannot be zero")
            raise ValueError("Transaction amount cannot be zero")
        return v
