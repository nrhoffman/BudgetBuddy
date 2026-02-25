"""
Transaction mapping and sorting utilities.

This module provides helper functions for working with transaction data
retrieved from external banking providers (e.g., Plaid).

Functions:
- sort_transactions(txns): Deterministically sorts Transaction objects.
- map_plaid_transaction(txn, account_type): Maps a Plaid transaction
  object into the internal Transaction domain model.

This module centralizes ingestion-layer transformation logic.
Derived flags (ACH detection, recurring detection, transfer detection)
should be handled in a higher-level service layer.
"""

from app.models.transaction import PlaidCategoryVersion, Transaction


def sort_transactions(txns: list[Transaction]) -> list[Transaction]:
    """
    Sort transactions deterministically by posted date and transaction ID.

    Args:
        txns: List of Transaction objects.

    Returns:
        Sorted list of transactions.
    """
    return sorted(txns, key=lambda t: (t.date, t.transaction_id))


def map_plaid_transaction(txn, account_type: str) -> Transaction:
    """
    Map a Plaid transaction object to the internal Transaction model.

    Args:
        txn: Plaid transaction object.
        account_type: Account subtype (checking, credit, etc.)

    Returns:
        Transaction: Normalized domain model instance.
    """

    category_primary, category_detailed, category_confidence, category_version = (
        _extract_category(txn)
    )

    plaid_category_version = _map_plaid_enum(
        category_version,
        PlaidCategoryVersion,
    )

    merchant_logo, merchant_confidence = _extract_counterparty(txn)

    (
        location_city,
        location_region,
        location_country,
        location_lat,
        location_lon,
        store_number,
    ) = _extract_location(txn)

    return Transaction(
        transaction_id=txn.transaction_id,
        account_id=txn.account_id,
        account_type=account_type,
        amount=txn.amount,
        iso_currency_code=getattr(txn, "iso_currency_code", None),
        unofficial_currency_code=getattr(txn, "unofficial_currency_code", None),
        date=txn.date,
        authorized_date=getattr(txn, "authorized_date", None),
        authorized_datetime=getattr(txn, "authorized_datetime", None),
        name=getattr(txn, "name", None),
        merchant_name=getattr(txn, "merchant_name", None),
        merchant_entity_id=getattr(txn, "merchant_entity_id", None),
        merchant_website=getattr(txn, "website", None),
        merchant_logo_url=merchant_logo,
        merchant_confidence_level=merchant_confidence,
        category_primary=category_primary,
        category_detailed=category_detailed,
        category_confidence_level=category_confidence,
        plaid_category_version=plaid_category_version,
        payment_channel=getattr(txn, "payment_channel", None),
        transaction_type=getattr(txn, "transaction_type", None),
        transaction_code=getattr(txn, "transaction_code", None),
        location_city=location_city,
        location_region=location_region,
        location_country=location_country,
        location_lat=location_lat,
        location_lon=location_lon,
        store_number=store_number,
        is_ach=None,
        is_transfer=None,
        is_internal_transfer=None,
        is_recurring=None,
        pending=getattr(txn, "pending", None),
    )


# --------------------
# Helper: Safe Enum Coercion
# --------------------
def _extract_category(txn):
    pfc = getattr(txn, "personal_finance_category", None)
    if not pfc:
        return None, None, None, None

    primary = getattr(pfc, "primary", None)
    detailed = getattr(pfc, "detailed", None)
    confidence = str(getattr(pfc, "confidence_level", None))
    version = getattr(pfc, "version", None)

    return primary, detailed, confidence, version

def _extract_counterparty(txn):
    counterparties = getattr(txn, "counterparties", None) or []
    counterparty = counterparties[0] if counterparties else None
    top_level_logo = getattr(txn, "logo_url", None)

    cp_logo = None
    cp_confidence = None

    if isinstance(counterparty, dict):
        cp_logo = counterparty.get("logo_url")
        cp_confidence = counterparty.get("confidence_level")
    else:
        cp_logo = getattr(counterparty, "logo_url", None)
        cp_confidence = getattr(counterparty, "confidence_level", None)

    return top_level_logo or cp_logo, cp_confidence

def _extract_location(txn):
    location = getattr(txn, "location", None)
    if not location:
        return (None,) * 6

    return (
        getattr(location, "city", None),
        getattr(location, "region", None),
        getattr(location, "country", None),
        getattr(location, "lat", None),
        getattr(location, "lon", None),
        getattr(location, "store_number", None),
    )

def _map_plaid_enum(value, enum_cls):
    if not value:
        return None

    raw_value = getattr(value, "value", value)

    try:
        return enum_cls(str(raw_value).strip().lower())
    except ValueError:
        return None
