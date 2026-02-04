"""
Tests for ORM to domain model conversions.

Validates that AccountORM and TransactionORM instances are correctly
converted to their respective domain models.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.db.account_orm import AccountORM
from app.db.transaction_orm import TransactionORM
from app.models.account import Account
from app.models.transaction import Transaction
from app.mappers.account_mapper import (
    orm_to_domain_account,
    orm_to_domain_transaction,
)


# -----------------------
# Helper: make timezone-aware datetime
# -----------------------
def make_dt(year, month, day, hour=0, minute=0):
    """Return UTC timezone-aware datetime."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


# -----------------------
# Parametrized test: transaction conversion
# -----------------------
@pytest.mark.parametrize(
    (
        "txn_id",
        "account_id",
        "amount",
        "date",
        "name",
        "merchant_name",
        "primary",
        "detailed",
        "confidence",
        "pending",
        "iso_code",
        "unofficial_code",
    ),
    [
        (
            "txn_001",
            "acc_001",
            100.0,
            make_dt(2026, 1, 23, 12, 0),
            "Groceries",
            "Whole Foods",
            "FOOD_AND_DRINK",
            "FOOD_AND_DRINK_GROCERIES",
            "HIGH",
            False,
            "USD",
            None,
        ),
        (
            "txn_002",
            "acc_001",
            -50.25,
            make_dt(2026, 1, 24, 15, 30),
            "Refund",
            "Amazon",
            None,
            None,
            None,
            False,
            "USD",
            None,
        ),
    ],
)
def test_orm_to_domain_transaction(
    txn_id,
    account_id,
    amount,
    date,
    name,
    merchant_name,
    primary,
    detailed,
    confidence,
    pending,
    iso_code,
    unofficial_code,
):
    """Ensure TransactionORM is converted to domain Transaction correctly."""
    orm_txn = TransactionORM(
        id=txn_id,
        account_id=account_id,
        amount=amount,
        date=date,
        name=name,
        merchant_name=merchant_name,
        category_primary=primary,
        category_detailed=detailed,
        category_confidence_level=confidence,
        pending=pending,
        iso_currency_code=iso_code,
        unofficial_currency_code=unofficial_code,
    )

    domain_txn = orm_to_domain_transaction(orm_txn)

    assert isinstance(domain_txn, Transaction)
    assert domain_txn.transaction_id == txn_id
    assert domain_txn.account_id == account_id
    assert domain_txn.amount == Decimal(amount)
    assert domain_txn.date == date
    assert domain_txn.name == name
    assert domain_txn.merchant_name == merchant_name
    assert domain_txn.category_primary == primary
    assert domain_txn.category_detailed == detailed
    assert domain_txn.category_confidence_level == confidence
    assert domain_txn.pending == pending
    assert domain_txn.iso_currency_code == iso_code
    assert domain_txn.unofficial_currency_code == unofficial_code


# -----------------------
# Test: account conversion with multiple transactions
# -----------------------
def test_orm_to_domain_account_multiple_transactions():
    """Ensure AccountORM with multiple transactions converts correctly."""
    txn1 = TransactionORM(
        id="txn_001",
        account_id="acc_001",
        amount=100.0,
        date=make_dt(2026, 1, 23),
        category_primary="FOOD_AND_DRINK",
        category_detailed="FOOD_AND_DRINK_GROCERIES",
        category_confidence_level="HIGH",
    )
    txn2 = TransactionORM(
        id="txn_002",
        account_id="acc_001",
        amount=-50.25,
        date=make_dt(2026, 1, 24),
    )

    orm_account = AccountORM(
        id="acc_001",
        name="Checking",
        type="depository",
        subtype=None,
        balance=1000.0,
        initial_balance=1000.0,
        transactions=[txn1, txn2],
    )

    domain_account = orm_to_domain_account(orm_account)

    assert isinstance(domain_account, Account)
    assert domain_account.id == "acc_001"
    assert domain_account.name == "Checking"
    assert domain_account.type == "depository"
    assert domain_account.subtype is None
    assert domain_account.balance == 1000.0
    assert len(domain_account.transactions) == 2
    assert all(isinstance(tx, Transaction) for tx in domain_account.transactions)


# -----------------------
# Test: account with no transactions
# -----------------------
def test_orm_to_domain_account_no_transactions():
    """Ensure AccountORM with no transactions converts to domain account."""
    orm_account = AccountORM(
        id="acc_002",
        name="Savings",
        type="depository",
        subtype=None,
        balance=500.0,
        initial_balance=500.0,
        transactions=[],
    )

    domain_account = orm_to_domain_account(orm_account)

    assert isinstance(domain_account, Account)
    assert domain_account.id == "acc_002"
    assert domain_account.transactions == []


# -----------------------
# Test: invalid transaction amount triggers exception
# -----------------------
def test_orm_to_domain_transaction_invalid_amount():
    """Ensure invalid amount in TransactionORM raises an exception."""
    txn = TransactionORM(
        id="txn_invalid",
        account_id="acc_003",
        amount="not_a_number",
        date=make_dt(2026, 1, 23),
    )

    with pytest.raises(Exception):
        orm_to_domain_transaction(txn)
