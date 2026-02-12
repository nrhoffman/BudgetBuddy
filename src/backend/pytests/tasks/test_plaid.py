import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from app.exceptions import ExternalServiceError
from app.tasks.plaid import sync_transactions

import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from app.exceptions import ExternalServiceError
from app.tasks.plaid import sync_transactions

@pytest.mark.parametrize(
    "token_exists,cursor_exists,added_txns,modified_txns,removed_txns",
    [
        (False, False, [], [], []),  # No token → should raise ExternalServiceError
        (True, False, [], [], []),   # Token exists, no transactions
        (
            True,
            True,
            [SimpleNamespace(account_id="acc1", amount=100, transaction_id="txn1")],
            [SimpleNamespace(account_id="acc1", amount=50, transaction_id="txn2")],
            ["txn3"]
        ),  # Token + transactions
    ]
)
@patch("app.tasks.plaid.build_plaid_sync_context")
@patch("app.tasks.plaid.SESSIONLOCAL")
def test_sync_transactions(
    mock_sessionlocal,
    mock_build_ctx,
    token_exists,
    cursor_exists,
    added_txns,
    modified_txns,
    removed_txns
):
    """Full working test for sync_transactions with all scenarios."""

    # --- Mock DB session ---
    mock_db = MagicMock()
    mock_sessionlocal.return_value = mock_db

    # --- Mock BankRepository ---
    mock_bank_repo = MagicMock()
    token = MagicMock(user_id="user123", access_token="access_abc", item_id="item_abc")
    mock_bank_repo.get_token_by_item_id.return_value = token if token_exists else None
    mock_bank_repo.get_cursor_by_item_id.return_value = MagicMock(cursor="cursor123") if cursor_exists else None

    # --- Mock PlaidSandbox ---
    mock_plaid = MagicMock()
    mock_plaid.get_transactions_sync.return_value = {
        "added": added_txns,
        "modified": modified_txns,
        "removed": removed_txns,
        "next_cursor": "next_cursor",
        "raw": {"dummy": "data"},
    }

    # --- Mock AccountService ---
    mock_account_service = MagicMock()

    # --- Mock RawProviderRepo ---
    mock_raw_repo = MagicMock()

    # --- Mock AccountRepo ---
    mock_account_repo = MagicMock()
    mock_account_repo.get_all_accounts_with_transactions.return_value = []

    # --- Build full mocked context ---
    mock_ctx = SimpleNamespace(
        bank_repo=mock_bank_repo,
        account_repo=mock_account_repo,
        plaid=mock_plaid,
        account_service=mock_account_service,
        raw_provider_repo=mock_raw_repo
    )
    mock_build_ctx.return_value = mock_ctx

    # --- Call the task ---
    if not token_exists:
        with pytest.raises(ExternalServiceError):
            sync_transactions.run(item_id="item_abc")
        mock_db.close.assert_called_once()
        return

    # Run task normally
    sync_transactions.run(item_id="item_abc")

    # --- Assertions ---
    mock_db.close.assert_called_once()

    # Plaid called with correct cursor
    expected_cursor = "cursor123" if cursor_exists else None
    mock_plaid.get_transactions_sync.assert_called_once_with(token.access_token, [], expected_cursor)

    # Transaction changes applied
    mock_account_service.apply_transaction_changes.assert_called_once_with(
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

    # RawProviderData saved
    mock_raw_repo.save.assert_called_once()
