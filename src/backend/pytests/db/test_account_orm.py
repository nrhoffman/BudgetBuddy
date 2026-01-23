import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from decimal import Decimal

from app.db.base import Base
from app.db.account_orm import AccountORM
from app.models.account import AccountType, AccountSubType
from app.db.transaction_orm import TransactionORM


# -----------------------
# Fixture: in-memory SQLite
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
# Parametrize account creation
# -----------------------
@pytest.mark.parametrize(
    "account_id, name, type_, subtype, balance, user_id",
    [
        ("acc_001", "Checking Account", AccountType.DEPOSITORY, AccountSubType.CHECKING, 1000.0, "user_001"),
        ("acc_002", "Savings Account", AccountType.DEPOSITORY, AccountSubType.SAVINGS, 2500.50, "user_002"),
        ("acc_003", "Loan Account", AccountType.LOAN, None, -5000.0, "user_003"),
    ]
)
def test_account_orm_creation(db_session, account_id, name, type_, subtype, balance, user_id):
    account = AccountORM(
        id=account_id,
        name=name,
        type=type_,
        subtype=subtype,
        balance=balance,
        user_id=user_id
    )
    db_session.add(account)
    db_session.commit()

    saved = db_session.query(AccountORM).filter_by(id=account_id).first()
    assert saved is not None
    assert saved.id == account_id
    assert saved.name == name
    assert saved.type == type_
    assert saved.subtype == subtype
    assert float(saved.balance) == float(balance)
    assert saved.user_id == user_id
    assert saved.transactions == []


# -----------------------
# Test adding transactions
# -----------------------
def test_account_transactions_relationship(db_session):
    account = AccountORM(
        id="acc_010",
        name="Investment",
        type=AccountType.INVESTMENT,
        subtype=None,
        balance=5000.0,
        user_id="user_010"
    )
    db_session.add(account)
    db_session.commit()

    txn = TransactionORM(
        id="txn_001",
        account_id=account.id,
        amount=100.0,
        date=datetime(2026, 1, 23, 12, 0, 0)
    )
    account.transactions.append(txn)
    db_session.commit()

    saved = db_session.query(AccountORM).filter_by(id="acc_010").first()
    assert len(saved.transactions) == 1
    assert saved.transactions[0].id == "txn_001"
    assert float(saved.transactions[0].amount) == 100.0


# -----------------------
# Test nullable subtype
# -----------------------
def test_account_nullable_subtype(db_session):
    account = AccountORM(
        id="acc_020",
        name="Other Account",
        type=AccountType.OTHER,
        subtype=None,
        balance=0.0,
        user_id="user_020"
    )
    db_session.add(account)
    db_session.commit()

    saved = db_session.query(AccountORM).filter_by(id="acc_020").first()
    assert saved.subtype is None
