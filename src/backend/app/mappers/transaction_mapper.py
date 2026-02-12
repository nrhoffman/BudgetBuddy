"""
Transaction mapping and sorting utilities.

This module provides helper functions for working with transaction data
retrieved from external banking providers, such as Plaid.

Functions:
- `sort_transactions(txns)`: Sorts a list of `Transaction` objects
  deterministically by date and transaction ID.
- `map_plaid_transaction(txn)`: Maps a Plaid transaction object to the
  domain `Transaction` model used internally in the application.

These utilities are intended to centralize transaction transformation
logic and ensure consistent ordering and mapping across services and tasks.
"""

from app.models.transaction import Transaction


def sort_transactions(txns: list[Transaction]) -> list[Transaction]:
    """
    Sort transactions deterministically by date and transaction ID.

    Args:
        txns (list[Transaction]): List of Transaction objects.

    Returns:
        list[Transaction]: Sorted list of transactions.
    """
    return sorted(txns, key=lambda t: (t.date, t.transaction_id))


def map_plaid_transaction(txn, account_type) -> Transaction:
    """
    Map a Plaid transaction object to the Transaction domain model.

    Args:
        txn: Plaid transaction object.

    Returns:
        Transaction: Mapped Transaction domain model.
    """
    pfc = getattr(txn, "personal_finance_category", None)

    txn_date = txn.date
    if hasattr(txn_date, "date"):
        txn_date = txn_date.date()

    confidence = getattr(pfc, "confidence_level", None) if pfc else None
    if confidence is not None:
        confidence = str(confidence)

    return Transaction(
        transaction_id=txn.transaction_id,
        account_id=txn.account_id,
        account_type=account_type,
        name=txn.name,
        merchant_name=getattr(txn, "merchant_name", None),
        amount=txn.amount,
        date=txn_date,
        category_primary=getattr(pfc, "primary", None) if pfc else None,
        category_detailed=getattr(pfc, "detailed", None) if pfc else None,
        category_confidence_level=confidence,
        pending=getattr(txn, "pending", None),
        iso_currency_code=getattr(txn, "iso_currency_code", None),
        unofficial_currency_code=getattr(txn, "unofficial_currency_code", None),
    )
