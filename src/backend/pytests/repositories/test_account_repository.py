import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.account_orm import AccountORM
from app.db.transaction_orm import TransactionORM
from app.models.account import Account
from app.repositories.account_repository import AccountRepository

# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def repo(db_session):
    return AccountRepository(db_session)


# -----------------------------
# Helpers
# -----------------------------

def create_account(
    repo,
    db_session,
    *,
    acc_id="acc",
    user_id="user",
    acc_type="depository",
    balance=Decimal("100"),
    import_date=datetime(2026, 1, 2),
):
    account = Account(
        id=acc_id,
        name="Test Account",
        type=acc_type,
        subtype=None,
        balance=balance,
    )
    repo.add_account(account, user_id)
    orm = db_session.query(AccountORM).filter_by(id=acc_id).one()
    orm.initial_import_completed_at = import_date
    db_session.commit()
    return orm


def add_tx(db_session, acc_id, amount, date, category, balance_after=None):
    tx = TransactionORM(
        id=f"tx_{acc_id}_{date.isoformat()}",
        account_id=acc_id,
        amount=Decimal(amount),
        date=date,
        category_primary=category,
        balance_after=balance_after,
    )
    db_session.add(tx)
    db_session.commit()
    return tx


# -----------------------------
# CRUD Tests
# -----------------------------

def test_add_get_update_delete_account(repo):
    acc = Account(id="a1", name="Checking", type="depository", subtype=None, balance=50)
    
    # Add
    repo.add_account(acc, "u1")
    fetched = repo.get("a1", "u1")
    assert fetched.name == "Checking"
    assert fetched.balance == 50

    # Update
    repo.update_account("a1", "u1", account_name="Updated", balance=75)
    updated = repo.get("a1", "u1")
    assert updated.name == "Updated"
    assert updated.balance == 75

    # Delete
    repo.delete_account("a1", "u1")
    with pytest.raises(ValueError):
        repo.get("a1", "u1")


# -----------------------------
# signed_amount
# -----------------------------

@pytest.mark.parametrize(
    "account_type, category, expected",
    [
        ("depository", "INCOME", 100),
        ("depository", "EXPENSE", -100),
        ("credit", "INCOME", -100),
        ("credit", "EXPENSE", 100),
        ("loan", "INCOME", -100),
        ("loan", "EXPENSE", 100),
    ]
)
def test_signed_amount(repo, account_type, category, expected):
    tx = TransactionORM(amount=Decimal("100"), category_primary=category)
    assert repo.signed_amount(tx, account_type) == Decimal(expected)


# -----------------------------
# recalculate_balances_backward
# -----------------------------

@pytest.mark.parametrize(
    "account_type, initial_balance, transactions, expected_balances",
    [
        (
            "depository",
            Decimal("100"),
            [("INCOME", "2026-01-01", 50), ("EXPENSE", "2026-01-03", 20)],
            [Decimal("100"), None],  # post-import tx untouched
        ),
        (
            "credit",
            Decimal("500"),
            [("INCOME", "2026-01-01", 100), ("EXPENSE", "2026-01-03", 50)],
            [Decimal("500"), None],
        ),
        (
            "depository",
            Decimal("200"),
            [("INCOME", "2026-01-03", 25)],
            [Decimal("200")],  # single tx becomes anchor
        ),
    ],
)
def test_recalculate_balances_backward(
    repo, db_session, account_type, initial_balance,
    transactions, expected_balances
):
    acc_id = "acc1"
    user_id = "user1"
    import_date = datetime(2026, 1, 2)

    create_account(
        repo,
        db_session,
        acc_id=acc_id,
        user_id=user_id,
        acc_type=account_type,
        balance=initial_balance,
        import_date=import_date,
    )

    for category, date_str, amount in transactions:
        add_tx(
            db_session,
            acc_id,
            amount,
            datetime.fromisoformat(date_str),
            category,
        )

    repo.recalculate_balances_backward(user_id, acc_id)

    stored = (
        db_session.query(TransactionORM)
        .filter(TransactionORM.account_id == acc_id)
        .order_by(TransactionORM.date)
        .all()
    )

    assert [tx.balance_after for tx in stored] == expected_balances


# -----------------------------
# recalculate_balances_from
# -----------------------------

def test_recalculate_balances_from(repo, db_session):
    acc_id = "acc2"
    user_id = "user2"
    import_date = datetime(2026, 1, 2)

    create_account(
        repo,
        db_session,
        acc_id=acc_id,
        user_id=user_id,
        acc_type="depository",
        balance=Decimal("100"),
        import_date=import_date,
    )

    add_tx(db_session, acc_id, 50, datetime(2026, 1, 1), "INCOME")
    add_tx(db_session, acc_id, 20, datetime(2026, 1, 3), "EXPENSE")

    boundary_dates = {
        acc_id: {
            "latest_before_import": import_date,
            "earliest_after_import": import_date,
        }
    }

    repo.recalculate_balances_from(user_id, boundary_dates)

    stored = (
        db_session.query(TransactionORM)
        .filter(TransactionORM.account_id == acc_id)
        .order_by(TransactionORM.date)
        .all()
    )

    # backward anchor, then forward apply
    assert [tx.balance_after for tx in stored] == [
        Decimal("100"),
        Decimal("80"),
    ]

    acc = db_session.query(AccountORM).filter_by(id=acc_id).one()
    assert acc.balance == Decimal("100")


# -----------------------------
# get_all_accounts_with_transactions
# -----------------------------

def test_get_all_accounts_with_transactions(repo, db_session):
    create_account(repo, db_session, acc_id="a1", user_id="u1")
    add_tx(db_session, "a1", 50, datetime(2026, 1, 1), "INCOME")
    add_tx(db_session, "a1", 20, datetime(2026, 1, 2), "EXPENSE")

    accounts = repo.get_all_accounts_with_transactions("u1")
    assert len(accounts) == 1
    account = accounts[0]
    assert account.id == "a1"
    assert len(account.transactions) == 2
    assert [tx.amount for tx in account.transactions] == [Decimal("50"), Decimal("20")]
