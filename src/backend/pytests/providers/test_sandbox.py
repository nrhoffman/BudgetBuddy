import pytest
from unittest.mock import MagicMock
from datetime import datetime, date
from app.providers.plaid_sandbox import PlaidSandbox
from app.models.account import Account
from app.models.transaction import Transaction


# -----------------------
# Fixture: PlaidSandbox instance with mocked client
# -----------------------
@pytest.fixture
def plaid_sandbox():
    provider = PlaidSandbox()
    provider.client = MagicMock()
    return provider


# -----------------------
# Parametrized test: create_link_token
# -----------------------
@pytest.mark.parametrize(
    "mock_token",
    ["mock_link_token", "another_token"]
)
def test_create_link_token(plaid_sandbox, mock_token):
    plaid_sandbox.client.link_token_create.return_value.link_token = mock_token
    token = plaid_sandbox.create_link_token("user_001")
    assert isinstance(token, str)
    assert token == mock_token


# -----------------------
# Parametrized test: exchange_public_token
# -----------------------
@pytest.mark.parametrize(
    "public_token, mock_access_token",
    [
        ("public_123", "access_123"),
        ("public_456", "access_456"),
    ]
)
def test_exchange_public_token(plaid_sandbox, public_token, mock_access_token):
    plaid_sandbox.client.item_public_token_exchange.return_value.access_token = mock_access_token
    access_token = plaid_sandbox.exchange_public_token(public_token)
    assert isinstance(access_token, str)
    assert access_token == mock_access_token


# -----------------------
# Parametrized test: get_accounts
# -----------------------
@pytest.mark.parametrize(
    "acc_id, name, type_, subtype, balance",
    [
        ("acc_001", "Checking", "depository", "checking", 100.0),
        ("acc_002", "Savings", "depository", "savings", 500.0),
        ("acc_003", "Credit Card", "credit", "student", -250.0),
    ]
)
def test_get_accounts(plaid_sandbox, acc_id, name, type_, subtype, balance):
    mock_account = MagicMock()
    mock_account.account_id = acc_id
    mock_account.name = name
    mock_account.type = type_
    mock_account.subtype = subtype
    mock_account.balances.current = balance

    plaid_sandbox.client.accounts_balance_get.return_value.accounts = [mock_account]
    accounts = plaid_sandbox.get_accounts("access_token_123")

    assert len(accounts) == 1
    acc = accounts[0]
    assert isinstance(acc, Account)
    assert acc.id == acc_id
    assert acc.name == name
    assert acc.type.value == type_
    assert acc.subtype.value == subtype
    assert acc.balance == balance


# -----------------------
# Parametrized test: get_transactions
# -----------------------
@pytest.mark.parametrize(
    "txn_id, acc_id, name, merchant, amount, date_val, category, pending, iso_code, unofficial_code",
    [
        ("txn_001", "acc_001", "Coffee", "Starbucks", 4.5, datetime(2026, 1, 23), ["Food", "Coffee"], False, "USD", None),
        ("txn_002", "acc_002", "Lunch", "Chipotle", 12.0, datetime(2026, 1, 24), ["Food", "Lunch"], True, "USD", None),
    ]
)
def test_get_transactions(plaid_sandbox, txn_id, acc_id, name, merchant, amount, date_val, category, pending, iso_code, unofficial_code):
    mock_txn = MagicMock()
    mock_txn.transaction_id = txn_id
    mock_txn.account_id = acc_id
    mock_txn.name = name
    mock_txn.merchant_name = merchant
    mock_txn.amount = amount
    mock_txn.date = date_val
    mock_txn.category = category
    mock_txn.pending = pending
    mock_txn.iso_currency_code = iso_code
    mock_txn.unofficial_currency_code = unofficial_code

    plaid_sandbox.client.transactions_get.return_value.transactions = [mock_txn]

    start_date = date(2026, 1, 1)
    end_date = date(2026, 1, 31)
    transactions = plaid_sandbox.get_transactions("access_token_123", start_date, end_date)

    assert len(transactions) == 1
    txn = transactions[0]
    assert isinstance(txn, Transaction)
    assert txn.transaction_id == txn_id
    assert txn.account_id == acc_id
    assert txn.name == name
    assert txn.merchant_name == merchant
    assert float(txn.amount) == amount
    assert txn.date == date_val
    assert txn.category == category
    assert txn.pending is pending
    assert txn.iso_currency_code == iso_code
    assert txn.unofficial_currency_code == unofficial_code
