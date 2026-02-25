"""
Domain models for financial transactions.

Includes Transaction and UpdateTransaction schemas with validation.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from app.logger import logger


class PlaidCategoryVersion(str, Enum):
    """
    Enum definitions for supported Plaid category taxonomy versions.
    """
    V1 = "v1"
    V2 = "v2"


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
    Rich domain model representing a normalized financial transaction.

    This model is designed to support:
    - Cash flow analysis
    - Merchant analytics
    - Recurring transaction detection
    - ACH and transfer classification
    - Financial forecasting
    - Behavioral spending analysis

    The model preserves key raw ingestion fields (merchant identity,
    payment metadata, Plaid categorization, and location data) while
    also supporting derived system flags (e.g., is_ach, is_transfer,
    is_recurring).

    Core Sections:

    1. Identifiers
       - transaction_id: Unique transaction identifier (aliased from "id").
       - account_id: Associated account identifier.
       - account_type: Account classification (checking, credit, etc.).

    2. Monetary Data
       - amount: Non-zero transaction value (positive or negative).
       - balance_after: Account balance after posting (if available).
       - iso_currency_code / unofficial_currency_code: Currency metadata.

    3. Temporal Data
       - date: Posted transaction timestamp.
       - authorized_date / authorized_datetime: Original authorization time.

    4. Merchant Metadata
       - name: Original transaction description.
       - merchant_name: Normalized merchant name.
       - merchant_entity_id: Stable merchant identifier.
       - merchant_website / merchant_logo_url: Optional enrichment.
       - merchant_confidence_level: Merchant match confidence.

    5. Categorization
       - category_primary / category_detailed: Internal categories.
       - category_confidence_level: Categorization confidence.
       - plaid_category_version: Version of upstream category taxonomy.

    6. Payment & Channel Metadata
       - payment_channel: online, in_store, other.
       - transaction_type: place, special, etc.
       - transaction_code: Network or processing code.

    7. Location Data
       - location_city / region / country: Merchant geography.
       - location_lat / location_lon: Coordinates (if available).
       - store_number: Merchant store identifier.

    8. Derived System Flags
       - is_ach: Indicates ACH-based transaction.
       - is_transfer: Indicates transfer (internal or external).
       - is_internal_transfer: Indicates movement between owned accounts.
       - is_recurring: Indicates detected recurring pattern.

    Notes:
        - Amount must not be zero.
        - Aliases allow ingestion from external APIs while preserving
          clean internal field names.
        - This model is suitable for analytics and business logic layers.
    """

    # --------------------
    # Core Identifiers
    # --------------------
    transaction_id: str = Field(..., alias="id")
    account_id: str
    account_type: Optional[str] = None

    # --------------------
    # Monetary Data
    # --------------------
    amount: Decimal
    iso_currency_code: Optional[str] = None
    unofficial_currency_code: Optional[str] = None
    balance_after: Optional[Decimal] = None

    # --------------------
    # Dates
    # --------------------
    date: datetime  # Posted date
    authorized_date: Optional[datetime] = None
    authorized_datetime: Optional[datetime] = None

    # --------------------
    # Merchant Information
    # --------------------
    name: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_entity_id: Optional[str] = None
    merchant_website: Optional[str] = None
    merchant_logo_url: Optional[str] = None
    merchant_confidence_level: Optional[str] = None

    # --------------------
    # Categorization
    # --------------------
    category_primary: Optional[str] = None
    category_detailed: Optional[str] = None
    category_confidence_level: Optional[str] = None

    plaid_category_version: PlaidCategoryVersion | None = None

    # --------------------
    # Payment Metadata
    # --------------------
    payment_channel: Optional[str] = None  # online, in_store, other
    transaction_type: Optional[str] = None  # place, special, etc.
    transaction_code: Optional[str] = None

    # --------------------
    # Location Data
    # --------------------
    location_city: Optional[str] = None
    location_region: Optional[str] = None
    location_country: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    store_number: Optional[str] = None

    # --------------------
    # System Flags (Derived)
    # --------------------
    is_ach: Optional[bool] = None
    is_transfer: Optional[bool] = None
    is_internal_transfer: Optional[bool] = None
    is_recurring: Optional[bool] = None

    pending: Optional[bool] = None

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
