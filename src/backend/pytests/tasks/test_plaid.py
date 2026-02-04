import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from app.tasks.plaid import sync_transactions


@pytest.mark.parametrize(
    "token_exists,cursor_exists,added_txns,modified_txns,removed_txns",
    [
        (False, False, [], [], []),  # No token
        (True, False, [], [], []),   # Token exists, no transactions
        (
            True,
            True,
            [SimpleNamespace(account_id="acc1", amount=100, transaction_id="txn1")],
            [SimpleNamespace(account_id="acc1", amount=50, transaction_id="txn2")],
            ["txn3"]
        ),  # Token + transactions
    ],
)
@patch("app.tasks.plaid.SESSIONLOCAL")
@patch("app.tasks.plaid.PlaidSandbox")
@patch("app.tasks.plaid.BankRepository")
@patch("app.tasks.plaid.AccountService")
@patch("app.tasks.plaid.AccountRepository")
@patch("app.tasks.plaid.TransactionRepository")
def test_sync_transactions(
    mock_tx_repo_cls,
    mock_acc_repo_cls,
    mock_account_service_cls,
    mock_bank_repo_cls,
    mock_plaid_cls,
    mock_sessionlocal,
    token_exists,
    cursor_exists,
    added_txns,
    modified_txns,
    removed_txns,
):
    """
    Test sync_transactions Celery task with different scenarios:
    - No token
    - Token exists but no transactions
    - Token exists with added, modified, and removed transactions
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
    mock_plaid.get_transactions_sync.return_value = {
        "added": added_txns,
        "modified": modified_txns,
        "removed": removed_txns,
        "next_cursor": "next_cursor"
    }

    # Mock AccountService instance
    mock_account_service_instance = MagicMock()
    mock_account_service_cls.return_value = mock_account_service_instance

    # Mock repositories (just needed for instantiation)
    mock_acc_repo_cls.return_value = MagicMock()
    mock_tx_repo_cls.return_value = MagicMock()

    # Call task
    sync_transactions("item_abc")

    # Ensure DB session closed
    mock_db.close.assert_called_once()

    if not token_exists:
        mock_bank_repo.get_cursor_by_item_id.assert_not_called()
        mock_plaid.get_transactions_sync.assert_not_called()
        mock_account_service_instance.apply_transaction_changes.assert_not_called()
        return

    # Token exists → check Plaid called
    expected_cursor = "cursor123" if cursor_exists else None
    mock_plaid.get_transactions_sync.assert_called_once_with(token.access_token, expected_cursor)

    # Added/modified/removed transactions applied
    mock_account_service_instance.apply_transaction_changes.assert_called_once_with(
        user_id=token.user_id,
        added=added_txns,
        modified=modified_txns,
        removed=removed_txns,
    )

    # Cursor saved
    mock_bank_repo.save_cursor.assert_called_once_with(
        user_id=token.user_id,
        item_id="item_abc",
        cursor="next_cursor"
    )
