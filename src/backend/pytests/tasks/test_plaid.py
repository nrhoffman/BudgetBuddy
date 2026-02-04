import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from app.tasks.plaid import sync_transactions


@pytest.mark.parametrize(
    "token_exists,cursor_exists,added_txns",
    [
        (False, False, []),  # No token
        (True, False, []),   # Token exists, no tx
        (True, True, [SimpleNamespace(account_id="acc1", amount=100)]),  # Token + tx
    ],
)
@patch("app.tasks.plaid.SESSIONLOCAL")
@patch("app.tasks.plaid.PlaidSandbox")
@patch("app.tasks.plaid.BankRepository")
@patch("app.tasks.plaid.AccountService")
def test_sync_transactions(
    mock_account_service,
    mock_bank_repo_cls,
    mock_plaid_cls,
    mock_sessionlocal,
    token_exists,
    cursor_exists,
    added_txns,
):
    """
    Test sync_transactions task with different scenarios:
      - No token
      - Token exists but no transactions
      - Token exists with added transactions
    """
    # Mock DB session
    mock_db = MagicMock()
    mock_sessionlocal.return_value = mock_db

    # Mock bank repository instance
    mock_bank_repo = MagicMock()
    mock_bank_repo_cls.return_value = mock_bank_repo

    # Mock token
    token = MagicMock()
    token.user_id = "user123"
    token.access_token = "access_abc"
    token.item_id = "item_abc"

    mock_bank_repo.get_token_by_item_id.return_value = token if token_exists else None
    mock_bank_repo.get_cursor_by_item_id.return_value = MagicMock(cursor="cursor123") if cursor_exists else None

    # Mock PlaidSandbox
    mock_plaid = MagicMock()
    mock_plaid_cls.return_value = mock_plaid
    mock_plaid.get_transactions_sync.return_value = {"added": added_txns, "modified": [], "removed": [], "next_cursor": "next_cursor"}

    # Mock AccountService
    mock_account_service_instance = MagicMock()
    mock_account_service.return_value = mock_account_service_instance

    # Call task
    sync_transactions("item_abc")

    # DB session closed
    mock_db.close.assert_called_once()

    if not token_exists:
        mock_bank_repo.get_cursor_by_item_id.assert_not_called()
        mock_plaid.get_transactions_sync.assert_not_called()
        mock_account_service_instance.add_transaction.assert_not_called()
        return

    # Token exists → check Plaid called
    mock_plaid.get_transactions_sync.assert_called_once_with(token.access_token, "cursor123" if cursor_exists else None)

    # Added transactions applied
    if added_txns:
        for txn in added_txns:
            mock_account_service_instance.add_transaction.assert_any_call(
                token.user_id, txn.account_id, txn
            )
    else:
        mock_account_service_instance.add_transaction.assert_not_called()
