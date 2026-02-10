from datetime import date
import pytest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from app.providers.plaid_sandbox import PlaidSandbox
from app.models.account import Account
from app.models.transaction import Transaction

@pytest.fixture
def sandbox():
    return PlaidSandbox()


@pytest.mark.parametrize(
    "user_id, expected_token",
    [
        ("user_1", "link-token-123"),
        ("user_2", "link-token-456"),
    ],
)
def test_create_link_token(sandbox, user_id, expected_token):
    mock_response = MagicMock()
    mock_response.link_token = expected_token

    with patch.object(sandbox.client, "link_token_create", return_value=mock_response):
        token = sandbox.create_link_token(user_id)
        assert token == expected_token


@pytest.mark.parametrize(
    "public_token, expected_access",
    [
        ("public-token-1", "access-token-1"),
        ("public-token-2", "access-token-2"),
    ],
)
def test_exchange_public_token(sandbox, public_token, expected_access):
    mock_response = MagicMock()
    mock_response.access_token = expected_access

    with patch.object(sandbox.client, "item_public_token_exchange", return_value=mock_response):
        res = sandbox.exchange_public_token(public_token)
        assert res.access_token == expected_access


@pytest.mark.parametrize(
    "access_token, expected_accounts",
    [
        ("access-token-1", [{"id": "a1", "balance": {"available": 100}}]),
        ("access-token-2", [{"id": "a2", "balance": {"available": 200}}]),
    ],
)
def test_get_accounts(sandbox, access_token, expected_accounts):
    mock_response = MagicMock()
    mock_response.accounts = expected_accounts

    with patch.object(sandbox.client, "accounts_balance_get", return_value=mock_response):
        res = sandbox.get_accounts(access_token)
        assert res.accounts == expected_accounts


@pytest.mark.parametrize(
    "access_token,start_date,end_date,expected_txns",
    [
        ("access-token-1", date(2026, 1, 1), date(2026, 1, 31), [{"transaction_id": "t1"}]),
        ("access-token-2", date(2026, 2, 1), date(2026, 2, 5), [{"transaction_id": "t2"}]),
    ],
)
def test_get_transactions(sandbox, access_token, start_date, end_date, expected_txns):
    mock_response = MagicMock()
    mock_response.transactions = expected_txns

    with patch.object(sandbox.client, "transactions_get", return_value=mock_response):
        res = sandbox.get_transactions(access_token, start_date, end_date)
        assert res.transactions == expected_txns

def test_get_transactions_sync(sandbox):
    # Provide accounts for the test
    accounts = [
        Account(
            id="a1",
            name="Checking",
            type="depository",
            subtype="checking",
            mask="1234",
            official_name="Chase Checking",
            balance=Decimal("1000.0")
        )
    ]

    # Mock two paginated responses from transactions_sync
    mock_response_1 = MagicMock()
    mock_response_1.added = [SimpleNamespace(account_id="a1", transaction_id="tx1")]
    mock_response_1.modified = []
    mock_response_1.removed = []
    mock_response_1.next_cursor = "cursor-1"
    mock_response_1.has_more = True
    mock_response_1.to_dict.return_value = {"page": 1}

    mock_response_2 = MagicMock()
    mock_response_2.added = [SimpleNamespace(account_id="a1", transaction_id="tx2")]
    mock_response_2.modified = []
    mock_response_2.removed = []
    mock_response_2.next_cursor = "cursor-2"
    mock_response_2.has_more = False
    mock_response_2.to_dict.return_value = {"page": 2}

    # Patch the client.transactions_sync method to return the mock responses
    with patch.object(sandbox.client, "transactions_sync", side_effect=[mock_response_1, mock_response_2]):
        # Patch the mapping function to return fully valid Transaction objects
        with patch("app.providers.plaid_sandbox.map_plaid_transaction") as mock_map:
            mock_map.side_effect = lambda tx, t: Transaction(
                transaction_id=tx.transaction_id,
                account_id=tx.account_id,
                account_type=t,
                amount=Decimal("50.0"),
                date=date.today()
            )

            # Call the method under test
            result = sandbox.get_transactions_sync("access-token", accounts)

            # Assertions
            assert len(result["added"]) == 2
            assert result["next_cursor"] == "cursor-2"
            assert len(result["raw"]) == 2