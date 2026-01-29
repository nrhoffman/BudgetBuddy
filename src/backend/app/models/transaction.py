"""
Pydantic models for representing financial transactions and transaction updates.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.logger import logger


class UpdateTransaction(BaseModel):
    """
    Payload for updating editable fields on an existing transaction.

    Only user-modifiable fields should be included here. Fields are optional
    to allow partial updates.
    
    Attributes:
        category_primary: High-level transaction category (e.g. "Food").
        category_detailed: More specific transaction category
            (e.g. "Restaurants").
    """
    category_primary: Optional[str] = None
    category_detailed: Optional[str] = None


class Transaction(BaseModel):
    """
    Represents a single financial transaction associated with an account.

    This model is used for reading and returning transaction data. Some fields
    originate from external providers (e.g. transaction name or merchant),
    while others may be user-defined or system-derived.

    Attributes:
        transaction_id: Unique identifier for the transaction.
        account_id: Identifier of the account this transaction belongs to.
        amount: Transaction amount. Must be non-zero.
        date: Date and time the transaction occurred.
        balance_after: Account balance immediately after this transaction,
            if available.
        name: Provider-supplied or cleaned transaction description.
        merchant_name: Normalized merchant name, if recognized.
        category_primary: High-level transaction category.
        category_detailed: More specific transaction category.
        category_confidence_level: Confidence level associated with the
            category assignment.
        pending: Indicates whether the transaction is pending.
        iso_currency_code: ISO 4217 currency code (e.g. "USD").
        unofficial_currency_code: Non-ISO currency code, if applicable.
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
    def amount_not_zero(cls, v: Decimal) -> Decimal:  # pylint: disable=no-self-argument
        """
        Validate that the transaction amount is not zero.
        """
        if v == 0:
            logger.debug("Validation failed: transaction amount cannot be zero")
            raise ValueError("Transaction amount cannot be zero")
        return v
