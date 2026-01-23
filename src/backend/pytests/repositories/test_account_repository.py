import pytest
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.account_orm import AccountORM
from app.db.transaction_orm import TransactionORM
from app.models.account import Account, AccountType
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository

# -----------------------
# Fixture: in-memory DB session
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
# Fixture: repository
# -----------------------
@pytest.fixture
def repo(db_session):
    return AccountRepository(db_session)


# -----------------------
# Parametrized test: add and get accounts
# -----------------------
@pytest.mark.parametrize(
    "account_id, name, type_, balance",
    [
        ("acc_001", "Test Account", AccountType.DEPOSITORY, 1000.0),
        ("acc_002", "Savings Account", AccountType.DEPOSITORY, 5000.0),
        ("acc_003", "Credit Card", AccountType.CREDIT, -250.0),
    ]
)
def test_add_and_get_account(repo, account_id, name, type_, balance):
    account = Account(
        id=account_id,
        name=name,
        type=type_,
        subtype=None,
        balance=balance,
        transactions=[]
    )

    repo.add_account(account, user_id="user_001")
    fetched = repo.get(account_id, "user_001")

    assert fetched.id == account.id
    assert fetched.name == account.name
    assert float(fetched.balance) == account.balance


# -----------------------
# Parametrized test: delete accounts
# -----------------------
@pytest.mark.parametrize(
    "account_id, initial_name",
    [
        ("acc_del1", "DeleteMe1"),
        ("acc_del2", "DeleteMe2"),
    ]
)
def test_delete_account(repo, db_session, account_id, initial_name):
    account = AccountORM(id=account_id, name=initial_name, type="depository", balance=500.0, user_id="user_001")
    db_session.add(account)
    db_session.commit()

    repo.delete_account(account_id, "user_001")
    with pytest.raises(ValueError):
        repo.get(account_id, "user_001")


# -----------------------
# Parametrized test: add transactions
# -----------------------
@pytest.mark.parametrize(
    "txn_id, account_id, amount, name, txn_date",
    [
        ("txn_001", "acc_txn1", Decimal("100.5"), "Groceries", datetime(2026, 1, 23, tzinfo=timezone.utc)),
        ("txn_002", "acc_txn2", Decimal("50.0"), "Coffee", datetime(2026, 1, 24, tzinfo=timezone.utc)),
    ]
)
def test_add_transaction(repo, db_session, txn_id, account_id, amount, name, txn_date):
    account = AccountORM(id=account_id, name="TxnAccount", type="depository", balance=800.0, user_id="user_001")
    db_session.add(account)
    db_session.commit()

    txn = Transaction(
        transaction_id=txn_id,
        account_id=account_id,
        amount=amount,
        date=txn_date,
        name=name
    )
    repo.add_transaction(account_id, txn, "user_001")

    fetched_account = repo.get(account_id, "user_001")
    assert len(fetched_account.transactions) == 1
    assert fetched_account.transactions[0].transaction_id == txn_id


# -----------------------
# Parametrized test: update accounts
# -----------------------
@pytest.mark.parametrize(
    "account_id, old_name, new_name, old_balance, new_balance",
    [
        ("acc_upd1", "OldName1", "NewName1", 300.0, 500.0),
        ("acc_upd2", "OldName2", "NewName2", 150.0, 250.0),
    ]
)
def test_update_account(repo, db_session, account_id, old_name, new_name, old_balance, new_balance):
    account = AccountORM(id=account_id, name=old_name, type="depository", balance=old_balance, user_id="user_001")
    db_session.add(account)
    db_session.commit()

    updated_account = Account(
        id=account_id, name=new_name, type=AccountType.DEPOSITORY, subtype=None, balance=new_balance, transactions=[]
    )
    repo.update(account_id, updated_account, "user_001")

    fetched = repo.get(account_id, "user_001")
    assert fetched.name == new_name
    assert float(fetched.balance) == new_balance


# -----------------------
# Test: get all accounts with transactions (can parametrize if desired)
# -----------------------
def test_get_all_accounts_with_transactions(repo, db_session):
    accounts_data = [
        ("acc_all1", "A1", 100.0, "txn101", 50.0, datetime(2026, 1, 1)),
        ("acc_all2", "A2", 200.0, "txn102", 150.0, datetime(2026, 1, 2)),
    ]

    for acc_id, acc_name, balance, txn_id, txn_amount, txn_date in accounts_data:
        acc = AccountORM(id=acc_id, name=acc_name, type="depository", balance=balance, user_id="user_002")
        txn = TransactionORM(id=txn_id, account_id=acc_id, amount=txn_amount, date=txn_date)
        acc.transactions.append(txn)
        db_session.add(acc)

    db_session.commit()

    accounts_fetched = repo.get_all_accounts_with_transactions("user_002")
    assert len(accounts_fetched) == 2
    assert all(len(acc.transactions) == 1 for acc in accounts_fetched)
