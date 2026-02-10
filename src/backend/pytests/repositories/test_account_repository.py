import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime, date

from app.repositories.account_repository import AccountRepository
from app.models.account import Account
from app.db.transaction_orm import TransactionORM
from app.db.account_orm import AccountORM


# ---------------------------
# Fixtures
# ---------------------------

@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def sample_account():
    return Account(
        id="acc_1",
        name="Checking",
        type="depository",
        subtype="checking",
        balance=100.0,
        initial_balance=100.0,
        initial_import_completed_at=datetime(2026, 2, 1)
    )


@pytest.fixture
def sample_tx():
    tx = MagicMock(spec=TransactionORM)
    tx.amount = Decimal("50.0")
    tx.direction = "in"
    tx.balance_after = None
    tx.date = date(2026, 2, 1)
    tx.account_id = "acc_1"
    return tx


# ---------------------------
# CRUD Tests
# ---------------------------

def test_add_account_calls_session_add(mock_session, sample_account):
    repo = AccountRepository(mock_session)
    repo.add_account(sample_account, user_id="user_1")
    assert mock_session.add.called


def test_get_account_found(mock_session, sample_account):
    orm = MagicMock(spec=AccountORM)
    with patch("app.repositories.account_repository.orm_to_domain_account", return_value=sample_account):
        mock_session.query.return_value.filter.return_value.first.return_value = orm
        repo = AccountRepository(mock_session)
        acc = repo.get("acc_1", "user_1")
        assert acc == sample_account


def test_get_account_not_found_raises(mock_session):
    mock_session.query.return_value.filter.return_value.first.return_value = None
    repo = AccountRepository(mock_session)
    with pytest.raises(ValueError):
        repo.get("acc_1", "user_1")


@pytest.mark.parametrize(
    "account_name,balance",
    [
        ("New Name", 200.0),
        (None, 150.0),
        ("Another Name", None),
        (None, None),
    ]
)
def test_update_account_sets_fields(mock_session, account_name, balance, sample_account):
    orm = MagicMock(spec=AccountORM)
    mock_session.query.return_value.filter.return_value.first.return_value = orm
    repo = AccountRepository(mock_session)
    repo.update_account("acc_1", "user_1", account_name=account_name, balance=balance)
    if account_name is not None:
        assert orm.name == account_name
    if balance is not None:
        assert orm.balance == balance


def test_update_account_not_found_raises(mock_session):
    mock_session.query.return_value.filter.return_value.first.return_value = None
    repo = AccountRepository(mock_session)
    with pytest.raises(ValueError):
        repo.update_account("acc_1", "user_1", account_name="X")


def test_delete_account_calls_delete(mock_session):
    orm = MagicMock(spec=AccountORM)
    mock_session.query.return_value.filter.return_value.first.return_value = orm
    repo = AccountRepository(mock_session)
    repo.delete_account("acc_1", "user_1")
    assert mock_session.delete.called


def test_delete_account_not_found_raises(mock_session):
    mock_session.query.return_value.filter.return_value.first.return_value = None
    repo = AccountRepository(mock_session)
    with pytest.raises(ValueError):
        repo.delete_account("acc_1", "user_1")


# ---------------------------
# Signed amount tests
# ---------------------------

@pytest.mark.parametrize("direction,expected", [("in", 50.0), ("out", -50.0)])
def test_signed_amount(direction, expected):
    tx = MagicMock(spec=TransactionORM)
    tx.amount = Decimal("50.0")
    tx.direction = direction
    repo = AccountRepository(MagicMock())
    assert repo.signed_amount(tx) == Decimal(expected)


# ---------------------------
# Recalculate balances tests
# ---------------------------

def test_recalculate_balances_backward_sets_balances(mock_session, sample_account, sample_tx):
    repo = AccountRepository(mock_session)
    with patch.object(repo, "get", return_value=sample_account), \
         patch.object(repo, "signed_amount", return_value=Decimal("50.0")):
        mock_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_tx]
        repo.recalculate_balances_backward("user_1", "acc_1")
        assert sample_tx.balance_after is not None


def test_recalculate_balances_from_calls_methods(mock_session, sample_account, sample_tx):
    repo = AccountRepository(mock_session)
    boundary_dates = {
        "acc_1": {
            "latest_before_import": datetime(2026, 1, 1),
            "earliest_after_import": datetime(2026, 2, 1),
        }
    }

    # Patch helper methods
    with patch.object(repo, "recalculate_balances_backward") as mock_backward, \
         patch.object(repo, "get", return_value=sample_account), \
         patch.object(repo, "signed_amount", return_value=Decimal("50.0")):

        # Patch prev_tx to have numeric balance_after
        mock_prev_tx = MagicMock(spec=TransactionORM)
        mock_prev_tx.balance_after = Decimal("100.0")
        mock_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.first.return_value = mock_prev_tx

        # Patch transactions list
        sample_tx.balance_after = Decimal("0")
        mock_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_tx]

        repo.recalculate_balances_from("user_1", boundary_dates)
        assert mock_backward.called
        assert sample_tx.balance_after is not None
        assert sample_account.balance is not None
    

def test_recalculate_balances_from_prev_tx_none_fixed(mock_session, sample_account, sample_tx):
    """
    Test the branch where prev_tx.balance_after is None,
    so last_before_tx is used to set running_balance.
    """
    repo = AccountRepository(mock_session)
    boundary_dates = {
        "acc_1": {
            "latest_before_import": None,
            "earliest_after_import": datetime(2026, 2, 1),
        }
    }

    # Patch get() to return sample account
    with patch.object(repo, "get", return_value=sample_account), \
         patch.object(repo, "signed_amount", return_value=Decimal("50.0")):

        # prev_tx exists but balance_after is None
        mock_prev_tx = MagicMock(spec=TransactionORM)
        mock_prev_tx.balance_after = None

        # last_before_tx has a **real numeric balance**
        mock_last_before_tx = MagicMock(spec=TransactionORM)
        mock_last_before_tx.balance_after = Decimal("200.0")  # <--- this is key

        # Patch query chain
        # First `.first()` call -> prev_tx, second `.first()` call -> last_before_tx
        mock_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.first.side_effect = [
            mock_prev_tx,       # prev_tx
        ]
        # The query for last_before_tx does not use join, so patch separately
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_last_before_tx

        # Patch the list of transactions returned for walk-forward update
        sample_tx.balance_after = Decimal("0")
        mock_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_tx]

        repo.recalculate_balances_from("user_1", boundary_dates)
        assert sample_tx.balance_after is not None
        assert sample_account.balance is not None


def test_recalculate_balances_backward_no_old_txs(mock_session, sample_account):
    """
    Test the branch where old_txs is empty,
    so first_tx is used and balance_after is set from initial_balance.
    """
    repo = AccountRepository(mock_session)

    # Patch get() to return sample account
    with patch.object(repo, "get", return_value=sample_account), \
         patch.object(repo, "signed_amount", return_value=Decimal("50.0")):

        # Simulate no old transactions
        mock_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = []

        # Patch first_tx to exist
        mock_first_tx = MagicMock(spec=TransactionORM)
        mock_first_tx.balance_after = None
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_first_tx

        repo.recalculate_balances_backward("user_1", "acc_1")
        assert mock_first_tx.balance_after == sample_account.initial_balance



# ---------------------------
# Query helpers
# ---------------------------

def test_get_all_accounts_with_transactions(mock_session):
    orm = MagicMock(spec=AccountORM)
    with patch(
        "app.repositories.account_repository.orm_to_domain_account",
        return_value=Account(
            id="a",
            name="n",
            type="depository",
            subtype="checking",
            balance=0.0,
            initial_balance=0.0,
            initial_import_completed_at=datetime.now()
        ),
    ):
        mock_session.query.return_value.filter.return_value.options.return_value.all.return_value = [orm]
        repo = AccountRepository(mock_session)
        accounts = repo.get_all_accounts_with_transactions("user_1")
        assert len(accounts) == 1

