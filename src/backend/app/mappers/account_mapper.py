"""
Convert ORM models to domain models.

Provides utility functions to transform AccountORM and TransactionORM instances
into their corresponding domain model representations.
"""

from decimal import Decimal

from app.logger import logger
from app.db.account_orm import AccountORM
from app.db.transaction_orm import TransactionORM
from app.models.account import Account
from app.models.transaction import Transaction


def orm_to_domain_account(orm: AccountORM) -> Account:
    """
    Convert an AccountORM instance to a domain Account.

    Args:
        orm (AccountORM): The ORM account object.

    Returns:
        Account: The domain account object.

    Raises:
        Exception: If conversion fails.
    """
    try:
        return Account(
            id=orm.id,
            name=orm.name,
            type=orm.type,
            subtype=orm.subtype,
            balance=float(orm.balance),
            transactions=[orm_to_domain_transaction(tx) for tx in orm.transactions],
        )
    except Exception:  # pylint: disable=broad-except
        logger.error(
            "Failed to convert AccountORM to Account",
            extra={"account_id": getattr(orm, "id", None)},
            exc_info=True,
        )
        raise


def orm_to_domain_transaction(orm: TransactionORM) -> Transaction:
    """
    Convert a TransactionORM instance to a domain Transaction.

    Args:
        orm (TransactionORM): The ORM transaction object.

    Returns:
        Transaction: The domain transaction object.

    Raises:
        Exception: If conversion fails.
    """
    try:
        return Transaction(
            transaction_id=orm.id,
            account_id=orm.account_id,
            amount=Decimal(orm.amount),
            date=orm.date,
            name=orm.name,
            merchant_name=orm.merchant_name,
            category_primary=orm.category_primary,
            category_detailed=orm.category_detailed,
            category_confidence_level=orm.category_confidence_level,
            pending=orm.pending,
            iso_currency_code=orm.iso_currency_code,
            unofficial_currency_code=orm.unofficial_currency_code,
        )
    except Exception:  # pylint: disable=broad-except
        logger.error(
            "Failed to convert TransactionORM to Transaction",
            extra={"transaction_id": getattr(orm, "id", None)},
            exc_info=True,
        )
        raise
