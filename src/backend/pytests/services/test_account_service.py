import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.models.account import Account
from app.models.transaction import Transaction
from app.services.account_service import AccountService
from app.repositories.account_repository import AccountRepository

# -------------------------------
# Sample data
# -------------------------------
SAMPLE_ACCOUNT = Account(
    id="acc_1",
    name="Checking",
    type="depository",
    subtype=None,
    balance=1000.0,
    transactions=[]
)

SAMPLE_TRANSACTION = Transaction(
    account_id="acc_1", 
    transaction_id="txn_1",
    amount=50.0,
    date="2026-01-24",
    name="Coffee",
    merchant_name="Starbucks",
    category_primary="Food",
    category_detailed="Coffee",
    category_confidence_level="LOW",
    pending=False,
    iso_currency_code="USD",
    unofficial_currency_code=None
)

# -------------------------------
# Fixtures
# -------------------------------
@pytest.fixture
def mock_account_repo():
    return MagicMock(spec=AccountRepository)

@pytest.fixture
def account_service(mock_account_repo):
    return AccountService(account_repo=mock_account_repo)

# -------------------------------
# Tests for create_account
# -------------------------------
@pytest.mark.parametrize("db_error, expected_exception", [(False, None), (True, HTTPException)])
def test_create_account(account_service, mock_account_repo, db_error, expected_exception):
    if db_error:
        mock_account_repo.add_account.side_effect = SQLAlchemyError("DB error")
    else:
        mock_account_repo.add_account.return_value = None

    if expected_exception:
        with pytest.raises(expected_exception):
            account_service.create_account(SAMPLE_ACCOUNT, "user_1")
        mock_account_repo.add_account.assert_called_once_with(SAMPLE_ACCOUNT, "user_1")
    else:
        result = account_service.create_account(SAMPLE_ACCOUNT, "user_1")
        assert result["message"] == "Account created"
        assert result["account_id"] == SAMPLE_ACCOUNT.id

# -------------------------------
# Tests for get_account
# -------------------------------
@pytest.mark.parametrize("account_exists, expected_exception", [(True, None), (False, HTTPException)])
def test_get_account(account_service, mock_account_repo, account_exists, expected_exception):
    mock_account_repo.get.return_value = SAMPLE_ACCOUNT if account_exists else None

    if expected_exception:
        with pytest.raises(expected_exception):
            account_service.get_account("acc_1", "user_1")
    else:
        account = account_service.get_account("acc_1", "user_1")
        assert account.id == SAMPLE_ACCOUNT.id

# -------------------------------
# Tests for update_account
# -------------------------------
@pytest.mark.parametrize(
    "account_name,balance,expected_exception",
    [
        ("NewName", None, None),      # update name
        (None, 2000.0, None),         # update balance
        (None, None, HTTPException)   # no fields
    ]
)
def test_update_account(account_service, mock_account_repo, account_name, balance, expected_exception):
    if expected_exception is None:
        result = account_service.update_account(
            "acc_1",
            "user_1",
            account_name,
            balance,
        )
        assert result["message"] == "Account updated successfully"
    else:
        with pytest.raises(expected_exception):
            account_service.update_account("acc_1", "user_1", account_name, balance)

# -------------------------------
# Tests for remove_account
# -------------------------------
@pytest.mark.parametrize("repo_raises, expected_exception", [(None, None), (ValueError("Not found"), HTTPException)])
def test_remove_account(account_service, mock_account_repo, repo_raises, expected_exception):
    if repo_raises:
        mock_account_repo.delete_account.side_effect = repo_raises
    else:
        mock_account_repo.delete_account.return_value = None

    if expected_exception:
        with pytest.raises(expected_exception):
            account_service.remove_account("acc_1", "user_1")
    else:
        result = account_service.remove_account("acc_1", "user_1")
        assert result["message"] == "Account deleted successfully"

# -------------------------------
# Tests for add_transaction
# -------------------------------
@pytest.mark.parametrize("account_exists, db_error, expected_exception", [
    (True, False, None),      # success
    (False, False, HTTPException),  # account not found
    (True, True, HTTPException)     # db error
])
def test_add_transaction(account_service, mock_account_repo, account_exists, db_error, expected_exception):
    mock_account_repo.get.return_value = SAMPLE_ACCOUNT if account_exists else None

    if db_error:
        mock_account_repo.add_transaction.side_effect = SQLAlchemyError("DB error")
    else:
        mock_account_repo.add_transaction.return_value = None

    if expected_exception:
        with pytest.raises(expected_exception):
            account_service.add_transaction("user_1", "acc_1", SAMPLE_TRANSACTION)
    else:
        result = account_service.add_transaction("user_1", "acc_1", SAMPLE_TRANSACTION)
        assert result["message"] == "Transaction added"
        assert result["transaction_id"] == SAMPLE_TRANSACTION.transaction_id

# -------------------------------
# Tests for get_user_financial_snapshot
# -------------------------------
@pytest.mark.parametrize("db_error, expected_exception", [(False, None), (True, HTTPException)])
def test_get_user_financial_snapshot(account_service, mock_account_repo, db_error, expected_exception):
    if db_error:
        mock_account_repo.get_all_accounts_with_transactions.side_effect = SQLAlchemyError("DB error")
    else:
        mock_account_repo.get_all_accounts_with_transactions.return_value = [SAMPLE_ACCOUNT]

    if expected_exception:
        with pytest.raises(expected_exception):
            account_service.get_user_financial_snapshot("user_1")
    else:
        accounts = account_service.get_user_financial_snapshot("user_1")
        assert len(accounts) == 1
        assert accounts[0].id == SAMPLE_ACCOUNT.id
