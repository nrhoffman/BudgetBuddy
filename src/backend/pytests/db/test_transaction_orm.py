import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.account_orm import AccountORM
from app.db.transaction_orm import TransactionORM


# -----------------------
# Fixture: in-memory SQLite database
# -----------------------
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# -----------------------
# Helper to normalize datetimes for SQLite comparison
# -----------------------
def normalize_datetime(dt):
    """Make datetime timezone-aware UTC if naive."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# -----------------------
# Parametrized transaction creation test
# -----------------------
@pytest.mark.parametrize(
    "txn_id, account_id, amount, date, name, merchant_name, category, pending, iso_code, unofficial_code",
    [
        (
            "txn_001",
            "acc_001",
            100.0,
            datetime(2026, 1, 23, 12, 0, tzinfo=timezone.utc),
            "Groceries",
            "Whole Foods",
            ["Food", "Groceries"],
            False,
            "USD",
            None,
        ),
        (
            "txn_002",
            "acc_001",
            -50.25,
            datetime(2026, 1, 24, 15, 30, tzinfo=timezone.utc),
            "Refund",
            "Amazon",
            ["Shopping"],
            False,
            "USD",
            None,
        ),
        (
            "txn_003",
            "acc_002",
            200.0,
            datetime(2026, 1, 25, 9, 45, tzinfo=timezone.utc),
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
    date,
    name,
    merchant_name,
    category,
    pending,
    iso_code,
    unofficial_code,
):
    account = AccountORM(
        id=account_id,
        name="Test Account",
        type="depository",
        balance=1000.0,
        user_id="user_001",
    )
    db_session.add(account)
    db_session.commit()

    txn = TransactionORM(
        id=txn_id,
        account_id=account_id,
        amount=amount,
        date=date,
        name=name,
        merchant_name=merchant_name,
        category=category,
        pending=pending,
        iso_currency_code=iso_code,
        unofficial_currency_code=unofficial_code,
    )

    account.transactions.append(txn)
    db_session.commit()

    saved_txn = db_session.query(TransactionORM).filter_by(id=txn_id).first()
    assert saved_txn is not None
    assert saved_txn.id == txn_id
    assert saved_txn.account_id == account_id
    assert float(saved_txn.amount) == float(amount)

    assert normalize_datetime(saved_txn.date) == normalize_datetime(date)

    assert saved_txn.name == name
    assert saved_txn.merchant_name == merchant_name
    assert saved_txn.category == category
    assert saved_txn.pending == pending
    assert saved_txn.iso_currency_code == iso_code
    assert saved_txn.unofficial_currency_code == unofficial_code


# -----------------------
# Test default date is set automatically
# -----------------------
def test_transaction_orm_default_date(db_session):
    account = AccountORM(
        id="acc_010",
        name="Auto Date Account",
        type="credit",
        balance=500.0,
        user_id="user_010",
    )
    db_session.add(account)
    db_session.commit()

    txn = TransactionORM(
        id="txn_010",
        account_id="acc_010",
        amount=75.0,
    )
    account.transactions.append(txn)
    db_session.commit()

    saved_txn = db_session.query(TransactionORM).filter_by(id="txn_010").first()
    assert saved_txn.date is not None

    saved_date = normalize_datetime(saved_txn.date)
    assert (datetime.now(timezone.utc) - saved_date).total_seconds() < 5
