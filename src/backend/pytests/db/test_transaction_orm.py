"""
Tests for the TransactionORM model.

Covers creation, nullable fields, relationships, and default timestamps.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.account_orm import AccountORM
from app.db.transaction_orm import TransactionORM
from app.models.account import AccountType


# -----------------------
# Fixture: in-memory SQLite database
# -----------------------
@pytest.fixture
def db_session():
    """Provide a SQLAlchemy session using in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    AccountORM.__table__.create(engine)
    TransactionORM.__table__.create(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


# -----------------------
# Helper: normalize datetime
# -----------------------
def normalize_datetime(value):
    """Ensure datetime is timezone-aware UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


# -----------------------
# Parametrized transaction creation
# -----------------------
@pytest.mark.parametrize(
    (
        "txn_id",
        "account_id",
        "amount",
        "balance_after",
        "date",
        "name",
        "merchant_name",
        "category_primary",
        "category_detailed",
        "category_confidence_level",
        "pending",
        "iso_code",
        "unofficial_code",
    ),
    [
        (
            "txn_001",
            "acc_001",
            Decimal("100.00"),
            Decimal("1100.00"),
            datetime(2026, 1, 23, 12, 0, tzinfo=timezone.utc),
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
            Decimal("-50.25"),
            Decimal("1049.75"),
            datetime(2026, 1, 24, 15, 30, tzinfo=timezone.utc),
            "Refund",
            "Amazon",
            "SHOPPING",
            "SHOPPING_ONLINE",
            "LOW",
            False,
            "USD",
            None,
        ),
        (
            "txn_003",
            "acc_002",
            Decimal("200.00"),
            Decimal("1200.00"),
            datetime(2026, 1, 25, 9, 45, tzinfo=timezone.utc),
            None,
            None,
            None,
            None,
            None,
            True,
            "USD",
            "USDX",
        ),
    ],
)
def test_transaction_orm_creation(
    db_session,
    txn_id,
    account_id,
    amount,
    balance_after,
    date,
    name,
    merchant_name,
    category_primary,
    category_detailed,
    category_confidence_level,
    pending,
    iso_code,
    unofficial_code,
):
    """Ensure transactions persist correctly with all fields."""
    account = AccountORM(
        id=account_id,
        name="Test Account",
        type=AccountType.DEPOSITORY,
        balance=Decimal("1000.00"),
        initial_balance=Decimal("1000.00"),
        user_id="user_001",
    )

    db_session.add(account)
    db_session.commit()

    transaction = TransactionORM(
        id=txn_id,
        account_id=account_id,
        account_type=account.type,  # ✅ Pass the account type
        amount=amount,
        balance_after=balance_after,
        date=date,
        name=name,
        merchant_name=merchant_name,
        category_primary=category_primary,
        category_detailed=category_detailed,
        category_confidence_level=category_confidence_level,
        pending=pending,
        iso_currency_code=iso_code,
        unofficial_currency_code=unofficial_code,
    )

    account.transactions.append(transaction)
    db_session.commit()

    saved = (
        db_session.query(TransactionORM)
        .filter_by(id=txn_id)
        .one()
    )

    assert saved.id == txn_id
    assert saved.account_id == account_id
    assert saved.account_type == account.type
    assert saved.amount == amount
    assert saved.balance_after == balance_after
    assert normalize_datetime(saved.date) == normalize_datetime(date)
    assert saved.name == name
    assert saved.merchant_name == merchant_name
    assert saved.category_primary == category_primary
    assert saved.category_detailed == category_detailed
    assert saved.category_confidence_level == category_confidence_level
    assert saved.pending == pending
    assert saved.iso_currency_code == iso_code
    assert saved.unofficial_currency_code == unofficial_code


# -----------------------
# Test default date behavior
# -----------------------
def test_transaction_orm_default_date(db_session):
    """Date should default to current UTC time when not provided."""
    account = AccountORM(
        id="acc_010",
        name="Auto Date Account",
        type=AccountType.CREDIT,
        balance=Decimal("500.00"),
        initial_balance=Decimal("500.00"),
        user_id="user_010",
    )

    db_session.add(account)
    db_session.commit()

    transaction = TransactionORM(
        id="txn_010",
        account_id="acc_010",
        account_type=account.type,  # ✅ Pass the account type
        amount=Decimal("75.00"),
        balance_after=Decimal("575.00"),
    )

    account.transactions.append(transaction)
    db_session.commit()

    saved = (
        db_session.query(TransactionORM)
        .filter_by(id="txn_010")
        .one()
    )

    saved_date = normalize_datetime(saved.date)
    now = datetime.now(timezone.utc)

    assert saved_date <= now
    assert (now - saved_date).total_seconds() < 5
