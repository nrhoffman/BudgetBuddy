import pytest
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.account_orm import AccountORM
from app.db.transaction_orm import TransactionORM
from app.models.account import AccountSubType, AccountType


# -----------------------
# Fixture: in-memory SQLite
# -----------------------
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    AccountORM.__table__.create(engine)
    TransactionORM.__table__.create(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


# -----------------------
# Parametrized account creation
# -----------------------
@pytest.mark.parametrize(
    (
        "account_id",
        "name",
        "account_type",
        "subtype",
        "balance",
        "initial_balance",
        "user_id",
    ),
    [
        (
            "acc_001",
            "Checking Account",
            AccountType.DEPOSITORY,
            AccountSubType.CHECKING,
            Decimal("1000.00"),
            Decimal("1000.00"),
            "user_001",
        ),
        (
            "acc_002",
            "Savings Account",
            AccountType.DEPOSITORY,
            AccountSubType.SAVINGS,
            Decimal("2500.50"),
            Decimal("2500.50"),
            "user_002",
        ),
        (
            "acc_003",
            "Loan Account",
            AccountType.LOAN,
            None,
            Decimal("-5000.00"),
            Decimal("-5000.00"),
            "user_003",
        ),
    ],
)
def test_account_orm_creation(
    db_session,
    account_id,
    name,
    account_type,
    subtype,
    balance,
    initial_balance,
    user_id,
):
    account = AccountORM(
        id=account_id,
        name=name,
        type=account_type,
        subtype=subtype,
        balance=balance,
        initial_balance=initial_balance,
        user_id=user_id,
    )

    db_session.add(account)
    db_session.commit()

    saved = (
        db_session.query(AccountORM)
        .filter_by(id=account_id)
        .one()
    )

    assert saved.id == account_id
    assert saved.name == name
    assert saved.type == account_type
    assert saved.subtype == subtype
    assert Decimal(saved.balance) == balance
    assert saved.initial_balance == initial_balance
    assert saved.user_id == user_id
    assert saved.transactions == []


# -----------------------
# Test transactions relationship
# -----------------------
def test_account_transactions_relationship(db_session):
    account = AccountORM(
        id="acc_010",
        name="Investment",
        type=AccountType.INVESTMENT,
        subtype=None,
        balance=Decimal("5000.00"),
        initial_balance=Decimal("5000.00"),
        user_id="user_010",
    )

    db_session.add(account)
    db_session.commit()

    transaction = TransactionORM(
        id="txn_001",
        account_id=account.id,
        account_type=account.type,  # ✅ Fix: pass account type
        amount=Decimal("100.00"),
        balance_after=Decimal("5100.00"),
        date=datetime(
            2026,
            1,
            23,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        ),
        name="Deposit",
        pending=False,
        iso_currency_code="USD",
    )

    account.transactions.append(transaction)
    db_session.commit()

    saved_account = (
        db_session.query(AccountORM)
        .filter_by(id="acc_010")
        .one()
    )

    assert len(saved_account.transactions) == 1

    saved_txn = saved_account.transactions[0]
    assert saved_txn.id == "txn_001"
    assert saved_txn.account_type == account.type  # ✅ Check account_type
    assert saved_txn.amount == Decimal("100.00")
    assert saved_txn.balance_after == Decimal("5100.00")
    assert saved_txn.name == "Deposit"
    assert saved_txn.pending is False
    assert saved_txn.iso_currency_code == "USD"


# -----------------------
# Test nullable subtype
# -----------------------
def test_account_nullable_subtype(db_session):
    account = AccountORM(
        id="acc_020",
        name="Other Account",
        type=AccountType.OTHER,
        subtype=None,
        balance=Decimal("0.00"),
        initial_balance=Decimal("0.00"),
        user_id="user_020",
    )

    db_session.add(account)
    db_session.commit()

    saved = (
        db_session.query(AccountORM)
        .filter_by(id="acc_020")
        .one()
    )

    assert saved.subtype is None
