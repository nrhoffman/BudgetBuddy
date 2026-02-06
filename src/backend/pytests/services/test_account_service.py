import pytest
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.models.account import Account
from app.models.transaction import Transaction
from app.services.account_service import AccountService


@pytest.fixture
def account_repo_mock(mocker):
    return mocker.Mock()


@pytest.fixture
def bank_repo_mock(mocker):
    return mocker.Mock()


@pytest.fixture
def txn_repo_mock(mocker):
    return mocker.Mock()


@pytest.fixture
def account_service(account_repo_mock, bank_repo_mock, txn_repo_mock):
    return AccountService(
        account_repo=account_repo_mock,
        bank_repo=bank_repo_mock,
        txn_repo=txn_repo_mock
    )


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
def sample_transaction_before_import():
    return Transaction(
        transaction_id="tx_before",
        account_id="acc1",
        date=datetime(2025, 12, 31),
        amount=Decimal("25.0"),
        description="Before Import Txn"
    )


@pytest.fixture
def sample_transaction_after_import():
    return Transaction(
        transaction_id="tx_after",
        account_id="acc1",
        date=datetime(2026, 2, 1),
        amount=Decimal("50.0"),
        description="After Import Txn"
    )


# ---------------------------
# create_account
# ---------------------------
@pytest.mark.parametrize("side_effect,expected_exception", [
    (None, None),
    (SQLAlchemyError("fail"), HTTPException),
])
def test_create_account(account_service, sample_account, account_repo_mock, side_effect, expected_exception):
    account_repo_mock.add_account.side_effect = side_effect
    if expected_exception:
        with pytest.raises(HTTPException):
            account_service.create_account(sample_account, "user1")
    else:
        result = account_service.create_account(sample_account, "user1")
        assert result["account_id"] == sample_account.id


# ---------------------------
# get_account
# ---------------------------
@pytest.mark.parametrize("repo_return,expected_exception,status_code", [
    ("found", None, None),
    (None, HTTPException, status.HTTP_404_NOT_FOUND),
    ("error", HTTPException, status.HTTP_500_INTERNAL_SERVER_ERROR)
])
def test_get_account(account_service, account_repo_mock, sample_account, repo_return, expected_exception, status_code):
    if repo_return == "found":
        account_repo_mock.get.return_value = sample_account
    elif repo_return == "error":
        account_repo_mock.get.side_effect = Exception("fail")
    else:
        account_repo_mock.get.return_value = None

    if expected_exception:
        with pytest.raises(HTTPException) as exc:
            account_service.get_account("acc1", "user1")
        assert exc.value.status_code == status_code
    else:
        result = account_service.get_account("acc1", "user1")
        assert result == sample_account


# ---------------------------
# update_account
# ---------------------------
@pytest.mark.parametrize("account_name,balance,expect_exception,status_code", [
    ("New Name", None, False, None),
    (None, 200.0, False, None),
    ("New Name", 200.0, False, None),
    (None, None, True, status.HTTP_400_BAD_REQUEST)
])
def test_update_account(account_service, account_repo_mock, account_name, balance, expect_exception, status_code):
    if expect_exception:
        with pytest.raises(HTTPException) as exc:
            account_service.update_account("acc1", "user1", account_name=account_name, balance=balance)
        assert exc.value.status_code == status_code
    else:
        account_repo_mock.update_account.return_value = None
        result = account_service.update_account("acc1", "user1", account_name=account_name, balance=balance)
        assert result["message"] == "Account updated successfully"


def test_update_account_exception(account_service, account_repo_mock):
    account_repo_mock.update_account.side_effect = Exception("fail")
    with pytest.raises(HTTPException) as exc:
        account_service.update_account("acc1", "user1", account_name="name")
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ---------------------------
# remove_account
# ---------------------------
@pytest.mark.parametrize("side_effect,expected_exception,status_code", [
    (None, False, None),
    (ValueError("Not found"), True, status.HTTP_404_NOT_FOUND),
    (Exception("fail"), True, status.HTTP_500_INTERNAL_SERVER_ERROR),
])
def test_remove_account(account_service, account_repo_mock, side_effect, expected_exception, status_code):
    account_repo_mock.delete_account.side_effect = side_effect
    if expected_exception:
        with pytest.raises(HTTPException) as exc:
            account_service.remove_account("acc1", "user1")
        assert exc.value.status_code == status_code
    else:
        result = account_service.remove_account("acc1", "user1")
        assert result["message"] == "Account deleted successfully"


# ---------------------------
# apply_transaction_changes
# ---------------------------
def test_apply_transaction_changes(account_service, txn_repo_mock, account_repo_mock, sample_transaction_after_import, sample_account):
    # Patch internal helpers to track calls
    account_service._remove_transactions = lambda user_id, removed: setattr(account_service, "removed_called", True)
    account_service._upsert_transactions = lambda user_id, txns: setattr(account_service, "upsert_called", True)
    account_service._rebalance_accounts = lambda user_id, boundaries: setattr(account_service, "rebalance_called", True)

    account_repo_mock.get.return_value = sample_account
    txn_repo_mock.get_by_ids.return_value = [sample_transaction_after_import]

    account_service.apply_transaction_changes(
        user_id="user1",
        added=[sample_transaction_after_import],
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
    txn_repo_mock.get_by_ids.return_value = [sample_transaction_before_import, sample_transaction_after_import]

    boundaries = account_service.find_earliest_dates(
        user_id="user1",
        added=[sample_transaction_before_import, sample_transaction_after_import],
        modified=[],
        removed=[]
    )

    assert "acc1" in boundaries
    assert boundaries["acc1"]["latest_before_import"] == sample_transaction_before_import.date
    assert boundaries["acc1"]["earliest_after_import"] == sample_transaction_after_import.date


# ---------------------------
# get_user_financial_snapshot
# ---------------------------
@pytest.mark.parametrize(
    "side_effect,expected_exception,status_code,result_value",
    [
        (None, False, None, ["account1"]),
        (SQLAlchemyError("fail"), True, status.HTTP_500_INTERNAL_SERVER_ERROR, None)
    ]
)
def test_get_user_financial_snapshot(
    account_service, account_repo_mock,
    side_effect, expected_exception, status_code, result_value
):
    account_repo_mock.get_all_accounts_with_transactions.side_effect = side_effect

    # Only set return_value if there is no side effect
    if side_effect is None:
        account_repo_mock.get_all_accounts_with_transactions.return_value = result_value

    if expected_exception:
        with pytest.raises(HTTPException) as exc:
            account_service.get_user_financial_snapshot("user1")
        assert exc.value.status_code == status_code
    else:
        result = account_service.get_user_financial_snapshot("user1")
        assert result == result_value
