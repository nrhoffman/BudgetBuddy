import pytest
from unittest.mock import patch
from decimal import Decimal
from datetime import datetime

from plaid import ApiException
from app.providers.plaid_sandbox import PlaidSandbox
from app.models.account import Account
from app.models.transaction import Transaction

# ---------------------------
# Fixture: PlaidSandbox instance
# ---------------------------
@pytest.fixture
def sandbox():
    return PlaidSandbox()


# ---------------------------
# Parametrize link token creation
# ---------------------------
@pytest.mark.parametrize(
    "user_id, expected_token",
    [
        ("user_001", "link-token-001"),
        ("user_002", "link-token-002"),
    ]
)
def test_create_link_token_success(sandbox, user_id, expected_token):
    mock_response = type("Resp", (), {"link_token": expected_token})()
    with patch.object(sandbox.client, "link_token_create", return_value=mock_response):
        token = sandbox.create_link_token(user_id)
        assert token == expected_token


def test_create_link_token_api_exception(sandbox):
    with patch.object(sandbox.client, "link_token_create", side_effect=ApiException("fail")):
        with pytest.raises(ApiException):
            sandbox.create_link_token("user_001")


def test_create_link_token_generic_exception(sandbox):
    with patch.object(sandbox.client, "link_token_create", side_effect=Exception("fail")):
        with pytest.raises(Exception):
            sandbox.create_link_token("user_001")


# ---------------------------
# Parametrize public token exchange
# ---------------------------
@pytest.mark.parametrize(
    "public_token, expected_access_token",
    [
        ("public-001", "access-001"),
        ("public-002", "access-002"),
    ]
)
def test_exchange_public_token_success(sandbox, public_token, expected_access_token):
    mock_response = type("Resp", (), {"access_token": expected_access_token})()
    with patch.object(sandbox.client, "item_public_token_exchange", return_value=mock_response):
        result = sandbox.exchange_public_token(public_token)
        assert result.access_token == expected_access_token


def test_exchange_public_token_api_exception(sandbox):
    with patch.object(sandbox.client, "item_public_token_exchange", side_effect=ApiException("fail")):
        with pytest.raises(ApiException):
            sandbox.exchange_public_token("public-001")


def test_exchange_public_token_generic_exception(sandbox):
    with patch.object(sandbox.client, "item_public_token_exchange", side_effect=Exception("fail")):
        with pytest.raises(Exception):
            sandbox.exchange_public_token("public-001")


# ---------------------------
# Parametrize accounts fetching
# ---------------------------
@pytest.mark.parametrize(
    "accounts_data",
    [
        [
            {"account_id": "acc1", "name": "Checking", "acct_type": "depository",
             "subtype": "checking", "balances": {"current": 100}},
            {"account_id": "acc2", "name": "Savings", "acct_type": "depository",
             "subtype": "savings", "balances": {"current": 500}},
        ],
        []
    ]
)
def test_get_accounts_success(sandbox, accounts_data):
    class MockAcc:
        def __init__(self, account_id, name, acct_type, subtype, balances):
            self.account_id = account_id
            self.name = name
            self.type = acct_type
            self.subtype = subtype
            self.balances = type('Balance', (), balances)()

    mock_response = type("Resp", (), {"accounts": [MockAcc(**acc) for acc in accounts_data]})()

    with patch.object(sandbox.client, "accounts_balance_get", return_value=mock_response):
        result = sandbox.get_accounts("fake-token")
        assert isinstance(result, list)
        if accounts_data:
            assert all(isinstance(acc, Account) for acc in result)
            assert [acc.id for acc in result] == [accd["account_id"] for accd in accounts_data]
        else:
            assert result == []


def test_get_accounts_api_exception(sandbox):
    with patch.object(sandbox.client, "accounts_balance_get", side_effect=ApiException("fail")):
        with pytest.raises(ApiException):
            sandbox.get_accounts("fake-token")


def test_get_accounts_generic_exception(sandbox):
    with patch.object(sandbox.client, "accounts_balance_get", side_effect=Exception("fail")):
        with pytest.raises(Exception):
            sandbox.get_accounts("fake-token")


# ---------------------------
# Parametrize transaction mapping
# ---------------------------
@pytest.mark.parametrize(
    "txn_data",
    [
        # Without personal_finance_category
        {"transaction_id": "txn1", "account_id": "acc1", "amount": Decimal("10.5"),
         "date": datetime(2026, 2, 3), "name": "Payment"},
        # With personal_finance_category
        {"transaction_id": "txn2", "account_id": "acc2", "amount": Decimal("50"),
         "date": datetime(2026, 2, 2), "name": "Salary",
         "personal_finance_category": {"primary":"INCOME","detailed":"Salary","confidence_level":0.9},
         "pending": True, "iso_currency_code": "USD", "unofficial_currency_code": None},
    ]
)
def test_map_plaid_transaction(sandbox, txn_data):
    class MockTxn:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    txn_kwargs = {k:v for k,v in txn_data.items() if k != "personal_finance_category"}
    mock_txn = MockTxn(**txn_kwargs)
    if "personal_finance_category" in txn_data:
        pfc_data = txn_data["personal_finance_category"]
        mock_txn.personal_finance_category = MockTxn(
            primary=pfc_data["primary"],
            detailed=pfc_data["detailed"],
            confidence_level=str(pfc_data["confidence_level"])  # convert to string
        )

    txn = sandbox.map_plaid_transaction(mock_txn)
    assert isinstance(txn, Transaction)
    assert txn.transaction_id == txn_data["transaction_id"]
    assert txn.amount == txn_data["amount"]
    if "personal_finance_category" in txn_data:
        assert txn.category_primary == "INCOME"
        assert txn.category_detailed == "Salary"
        assert txn.category_confidence_level == "0.9"
        assert txn.pending is True
        assert txn.iso_currency_code == "USD"


# ---------------------------
# Parametrize sorting transactions
# ---------------------------
@pytest.mark.parametrize(
    "txns, expected_order",
    [
        ([Transaction(transaction_id="2", account_id="a", amount=5, date=datetime(2026,2,2)),
          Transaction(transaction_id="1", account_id="a", amount=10, date=datetime(2026,2,1))],
         ["1", "2"]),
        ([Transaction(transaction_id="b", account_id="a", amount=5, date=datetime(2026,2,3)),
          Transaction(transaction_id="a", account_id="a", amount=5, date=datetime(2026,2,3))],
         ["a", "b"]),
    ]
)
def test_sort_transactions(sandbox, txns, expected_order):
    sorted_txns = sandbox.sort_transactions(txns)
    sorted_ids = [t.transaction_id for t in sorted_txns]
    assert sorted_ids == expected_order


# ---------------------------
# Parametrize incremental sync
# ---------------------------
@pytest.mark.parametrize(
    "pages",
    [
        # Single page
        ([{"added":[{"transaction_id":"a","account_id":"acc","amount":10,"date":datetime(2026,2,1)}],
           "modified": [], "removed": [], "has_more": False, "next_cursor": None}]),
        # Two pages
        ([
            {"added":[{"transaction_id":"x","account_id":"acc","amount":5,"date":datetime(2026,2,2)}],
            "modified": [], "removed": [], "has_more": True, "next_cursor": "c1"},
            {"added": [], "modified":[{"transaction_id":"y","account_id":"acc","amount":15,"date":datetime(2026,2,3)}],
            "removed":[{"transaction_id": "z"}], "has_more": False, "next_cursor": None}
        ]),
        # Empty results
        ([{"added": [], "modified": [], "removed": [], "has_more": False, "next_cursor": None}])
    ]
)
def test_get_transactions_sync(sandbox, pages):
    class MockTxn:
        def __init__(self, transaction_id, account_id, amount, date,
                     name="Test txn", merchant_name=None,
                     iso_currency_code="USD", unofficial_currency_code=None,
                     personal_finance_category=None, pending=None):
            self.transaction_id = transaction_id
            self.account_id = account_id
            self.amount = amount
            self.date = date
            self.name = name
            self.merchant_name = merchant_name
            self.iso_currency_code = iso_currency_code
            self.unofficial_currency_code = unofficial_currency_code
            self.personal_finance_category = personal_finance_category
            self.pending = pending

    # Patch transactions_sync to return proper MockTxn objects
    patched_pages = []
    for page in pages:
        patched_pages.append(
            type("Resp", (), {
                "added": [MockTxn(**tx) for tx in page["added"]],
                "modified": [MockTxn(**tx) for tx in page["modified"]],
                "removed": page["removed"],
                "has_more": page["has_more"],
                "next_cursor": page["next_cursor"]
            })()
        )

    with patch.object(sandbox.client, "transactions_sync", side_effect=patched_pages):
        result = sandbox.get_transactions_sync("fake-token")
        # Basic assertions
        assert "added" in result and isinstance(result["added"], list)
        assert "modified" in result and isinstance(result["modified"], list)
        assert "removed" in result and isinstance(result["removed"], list)
        # Check cumulative results
        expected_added = [tx["transaction_id"] for page in pages for tx in page["added"]]
        expected_modified = [tx["transaction_id"] for page in pages for tx in page["modified"]]
        expected_removed = [txn["transaction_id"] for page in pages for txn in page["removed"]]
        assert [t.transaction_id for t in result["added"]] == expected_added
        assert [t.transaction_id for t in result["modified"]] == expected_modified
        assert result["removed"] == expected_removed
        # Check next_cursor matches last page
        assert result["next_cursor"] == pages[-1]["next_cursor"]
