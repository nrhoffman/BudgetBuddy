import pytest
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException, status

from app.main import app
from app.models.account import Account
from app.models.transaction import Transaction
from app.services.account_service import AccountService
from app.routes.accounts import get_account_service, get_current_user


@pytest.fixture
def account_repo_mock(mocker):
    return mocker.Mock()


@pytest.fixture
def txn_repo_mock(mocker):
    return mocker.Mock()


@pytest.fixture
def account_service(account_repo_mock, txn_repo_mock):
    return AccountService(account_repo=account_repo_mock, txn_repo=txn_repo_mock)

@pytest.fixture
def mock_current_user():
    return "user1"

@pytest.fixture(autouse=True)
def override_dependencies(account_service, mock_current_user):
    app.dependency_overrides[get_account_service] = lambda: account_service
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    yield
    app.dependency_overrides.clear()



@pytest.fixture
def sample_account():
    return Account(
        id="acc1",
        name="Checking",
        balance=Decimal("100.0"),
        initial_import_completed_at=datetime(2026, 1, 1),
        transactions=[],
        type="depository",
        subtype="checking",
    )


@pytest.fixture
def sample_transaction():
    return Transaction(
        transaction_id="tx1",
        account_id="acc1",
        date=datetime(2026, 2, 1),
        amount=Decimal("50.0"),
        description="Test Txn"
    )

@pytest.fixture
def sample_transaction_before_import():
    return Transaction(
        transaction_id="tx_before",
        account_id="acc1",
        date=datetime(2025, 12, 31),  # BEFORE initial import
        amount=Decimal("25.0"),
        description="Before Import Txn"
    )

@pytest.fixture
def sample_transaction_after_import():
    return Transaction(
        transaction_id="tx_after",
        account_id="acc1",
        date=datetime(2026, 2, 1),  # AFTER initial import
        amount=Decimal("50.0"),
        description="After Import Txn"
    )

# ---------------------------
# create_account
# ---------------------------
def test_create_account_success(account_service, account_repo_mock, sample_account):
    account_repo_mock.add_account.return_value = None

    result = account_service.create_account(sample_account, user_id="user1")

    account_repo_mock.add_account.assert_called_once_with(sample_account, "user1")
    assert result["message"] == "Account created"
    assert result["account_id"] == sample_account.id


def test_create_account_failure(account_service, account_repo_mock, sample_account):
    from sqlalchemy.exc import SQLAlchemyError
    account_repo_mock.add_account.side_effect = SQLAlchemyError("DB Error")

    with pytest.raises(HTTPException) as exc:
        account_service.create_account(sample_account, "user1")
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ---------------------------
# get_account
# ---------------------------
def test_get_account_success(account_service, account_repo_mock, sample_account):
    account_repo_mock.get.return_value = sample_account

    result = account_service.get_account("acc1", "user1")
    assert result == sample_account


def test_get_account_not_found(account_service, account_repo_mock):
    account_repo_mock.get.return_value = None

    with pytest.raises(HTTPException) as exc:
        account_service.get_account("acc1", "user1")
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_account_exception(account_service, account_repo_mock):
    account_repo_mock.get.side_effect = Exception("fail")

    with pytest.raises(HTTPException) as exc:
        account_service.get_account("acc1", "user1")
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ---------------------------
# update_account
# ---------------------------
@pytest.mark.parametrize(
    "name,balance",
    [
        ("New Name", None),
        (None, 200.0),
        ("New Name", 200.0),
    ]
)
def test_update_account_success(account_service, account_repo_mock, name, balance):
    account_repo_mock.update_account.return_value = None
    result = account_service.update_account("acc1", "user1", account_name=name, balance=balance)
    assert result["message"] == "Account updated successfully"
    account_repo_mock.update_account.assert_called_once_with(account_id="acc1", user_id="user1", account_name=name, balance=balance)


def test_update_account_no_fields(account_service):
    with pytest.raises(HTTPException) as exc:
        account_service.update_account("acc1", "user1")
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


def test_update_account_exception(account_service, account_repo_mock):
    account_repo_mock.update_account.side_effect = Exception("fail")
    with pytest.raises(HTTPException) as exc:
        account_service.update_account("acc1", "user1", account_name="name")
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ---------------------------
# remove_account
# ---------------------------
def test_remove_account_success(account_service, account_repo_mock):
    account_repo_mock.delete_account.return_value = None
    result = account_service.remove_account("acc1", "user1")
    assert result["message"] == "Account deleted successfully"


def test_remove_account_not_found(account_service, account_repo_mock):
    account_repo_mock.delete_account.side_effect = ValueError("Account not found")
    with pytest.raises(HTTPException) as exc:
        account_service.remove_account("acc1", "user1")
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_remove_account_exception(account_service, account_repo_mock):
    account_repo_mock.delete_account.side_effect = Exception("fail")
    with pytest.raises(HTTPException) as exc:
        account_service.remove_account("acc1", "user1")
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ---------------------------
# apply_transaction_changes
# ---------------------------
def test_apply_transaction_changes_calls_helpers(account_service, txn_repo_mock, account_repo_mock, sample_transaction, sample_account):
    # Patch internal methods
    account_service._remove_transactions = lambda user_id, removed: setattr(account_service, "removed_called", True)
    account_service._upsert_transactions = lambda user_id, txns: setattr(account_service, "upsert_called", True)
    account_service._rebalance_accounts = lambda user_id, boundaries: setattr(account_service, "rebalance_called", True)

    # Make account repo return a real Account with datetime
    account_repo_mock.get.return_value = sample_account
    # Make txn repo return the transaction when queried
    txn_repo_mock.get_by_ids.return_value = [sample_transaction]

    account_service.apply_transaction_changes(
        user_id="user1",
        added=[sample_transaction],
        modified=[],
        removed=[]
    )

    assert getattr(account_service, "removed_called", False)
    assert getattr(account_service, "upsert_called", False)
    assert getattr(account_service, "rebalance_called", False)


# ---------------------------
# find_earliest_dates
# ---------------------------
def test_find_earliest_dates(account_service, account_repo_mock, txn_repo_mock,
                             sample_account, sample_transaction_before_import, sample_transaction_after_import):
    account_repo_mock.get.return_value = sample_account
    txn_repo_mock.get_by_ids.return_value = [
        sample_transaction_before_import,
        sample_transaction_after_import
    ]

    boundaries = account_service.find_earliest_dates(
        user_id="user1",
        added=[sample_transaction_before_import, sample_transaction_after_import],
        modified=[],
        removed=[]
    )

    assert "acc1" in boundaries
    # Now latest_before_import will be the transaction before initial import
    assert boundaries["acc1"]["latest_before_import"] == sample_transaction_before_import.date
    # earliest_after_import will be the transaction after initial import
    assert boundaries["acc1"]["earliest_after_import"] == sample_transaction_after_import.date


# ---------------------------
# get_user_financial_snapshot
# ---------------------------
def test_get_user_financial_snapshot_success(account_service, account_repo_mock):
    account_repo_mock.get_all_accounts_with_transactions.return_value = ["account1"]
    result = account_service.get_user_financial_snapshot("user1")
    assert result == ["account1"]


def test_get_user_financial_snapshot_exception(account_service, account_repo_mock):
    from sqlalchemy.exc import SQLAlchemyError
    account_repo_mock.get_all_accounts_with_transactions.side_effect = SQLAlchemyError("fail")
    with pytest.raises(HTTPException) as exc:
        account_service.get_user_financial_snapshot("user1")
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
