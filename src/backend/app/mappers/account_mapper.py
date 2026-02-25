"""
Convert ORM models to domain models.

Provides utility functions to transform AccountORM and TransactionORM instances
into their corresponding domain model representations.
"""

from decimal import Decimal

from app.db.account_orm import AccountORM
from app.db.transaction_orm import TransactionORM
from app.models.account import Account, parse_account_type, parse_account_subtype
from app.models.transaction import Transaction


def orm_to_domain_account(orm: AccountORM) -> Account:
    """
    Convert an AccountORM instance to a domain Account.

    Args:
        orm (AccountORM): The ORM account object.

    Returns:
        Account: The domain account object.
    """
    return Account(
        id=orm.id,
        name=orm.name,
        type=orm.type,
        subtype=orm.subtype,
        logo=orm.logo,

        balance=orm.balance,
        available_balance=orm.available_balance,
        credit_limit=orm.credit_limit,

        iso_currency_code=orm.iso_currency_code,
        unofficial_currency_code=orm.unofficial_currency_code,
        holder_category=orm.holder_category,

        initial_balance=orm.initial_balance,
        initial_import_completed_at=orm.initial_import_completed_at,

        apr=orm.apr,

        is_deleted=orm.is_deleted,
        deleted_at=orm.deleted_at,

        transactions=[
            orm_to_domain_transaction(tx)
            for tx in orm.transactions
        ],
    )


def orm_to_domain_transaction(orm: TransactionORM) -> Transaction:
    """
    Convert a TransactionORM instance to a domain Transaction.

    Args:
        orm (TransactionORM): The ORM transaction object.

    Returns:
        Transaction: The domain transaction object.
    """
    return Transaction(
        id=orm.id,
        account_id=orm.account_id,
        account_type=orm.account_type,

        amount=Decimal(orm.amount),
        balance_after=Decimal(orm.balance_after)
        if orm.balance_after is not None
        else None,

        iso_currency_code=orm.iso_currency_code,
        unofficial_currency_code=orm.unofficial_currency_code,

        date=orm.date,
        authorized_date=orm.authorized_date,
        authorized_datetime=orm.authorized_datetime,

        name=orm.name,
        merchant_name=orm.merchant_name,
        merchant_entity_id=orm.merchant_entity_id,
        merchant_website=orm.merchant_website,
        merchant_logo_url=orm.merchant_logo_url,
        merchant_confidence_level=orm.merchant_confidence_level,

        category_primary=orm.category_primary,
        category_detailed=orm.category_detailed,
        category_confidence_level=orm.category_confidence_level,
        plaid_category_version=orm.plaid_category_version,

        payment_channel=orm.payment_channel,
        transaction_type=orm.transaction_type,
        transaction_code=orm.transaction_code,

        location_city=orm.location_city,
        location_region=orm.location_region,
        location_country=orm.location_country,
        location_lat=orm.location_lat,
        location_lon=orm.location_lon,
        store_number=orm.store_number,

        is_ach=orm.is_ach,
        is_transfer=orm.is_transfer,
        is_internal_transfer=orm.is_internal_transfer,
        is_recurring=orm.is_recurring,

        pending=orm.pending,
    )


def map_plaid_account(
        account,
        institution_id: str,
        institution_logo: str | None = None
) -> Account:
    """
    Map a Plaid account object to a domain Account.

    Args:
        account: Raw Plaid account object from /accounts/balance/get.
        institution_logo (str | None): Optional logo URL for the institution.

    Returns:
        Account: Domain Account object.
    """
    balances = account.balances

    holder = getattr(account, "holder_category", None)
    holder_category = (
        holder.value if hasattr(holder, "value")
        else holder
    )

    return Account(
        id=account.account_id,
        name=account.name,
        type=parse_account_type(account.type),
        subtype=parse_account_subtype(account.subtype),
        logo=institution_logo,
        institution_id=institution_id,

        balance=account.balances.current,
        available_balance=balances.available if balances.available is not None else None,
        credit_limit=balances.limit if balances.limit is not None else None,

        iso_currency_code=balances.iso_currency_code,
        unofficial_currency_code=balances.unofficial_currency_code,

        holder_category=holder_category,

        transactions=[],
    )