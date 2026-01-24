import pytest
from datetime import datetime, date
from dataclasses import dataclass
from app.providers.plaid_sandbox import PlaidSandbox
from app.models.account import Account
from app.models.transaction import Transaction


# -----------------------
# Dataclasses to mock Plaid transactions
# -----------------------
@dataclass
class MockPersonalFinanceCategory:
    primary: str | None = None
    detailed: str | None = None
    confidence_level: str | None = None


@dataclass
class MockPlaidTransaction:
    transaction_id: str
    account_id: str
    name: str | None = None
    merchant_name: str | None = None
    amount: float = 0.0
    date: datetime = datetime.now()
    pending: bool | None = None
    iso_currency_code: str | None = None
    unofficial_currency_code: str | None = None
    personal_finance_category: MockPersonalFinanceCategory | None = None


# -----------------------
# Fixture: PlaidSandbox with mocked client
# -----------------------
@pytest.fixture
def plaid_sandbox():
    provider = PlaidSandbox()
    provider.client = type("MockClient", (), {})()  # empty object
    return provider

# -----------------------
# Test create_link_token
# -----------------------
@pytest.mark.parametrize("mock_token", ["mock_link_token", "another_token"])
def test_create_link_token(plaid_sandbox, mock_token):
    plaid_sandbox.client.link_token_create = lambda req: type("Resp", (), {"link_token": mock_token})()
    token = plaid_sandbox.create_link_token("user_001")
    assert isinstance(token, str)
    assert token == mock_token

# -----------------------
# Test exchange_public_token
# -----------------------
@pytest.mark.parametrize(
    "public_token, mock_access_token",
    [("public_123", "access_123"), ("public_456", "access_456")]
)
def test_exchange_public_token(plaid_sandbox, public_token, mock_access_token):
    plaid_sandbox.client.item_public_token_exchange = lambda req: type("Resp", (), {"access_token": mock_access_token})()
    access_token = plaid_sandbox.exchange_public_token(public_token)
    assert isinstance(access_token, str)
    assert access_token == mock_access_token

# -----------------------
# Test get_accounts
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
    class MockAccount:
        pass
    mock_account = MockAccount()
    mock_account.account_id = acc_id
    mock_account.name = name
    mock_account.type = type_
    mock_account.subtype = subtype
    mock_account.balances = type("Balances", (), {"current": balance})()

    plaid_sandbox.client.accounts_balance_get = lambda req: type("Resp", (), {"accounts": [mock_account]})()
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
# Test get_transactions
# -----------------------
@pytest.mark.parametrize(
    "txn_id, acc_id, name, merchant, amount, date_val, primary, detailed, confidence, pending, iso_code, unofficial_code",
    [
        ("txn_001", "acc_001", "Coffee", "Starbucks", 4.5, datetime(2026, 1, 23),
         "FOOD_AND_DRINK", "FOOD_AND_DRINK_COFFEE", "HIGH", False, "USD", None),
        ("txn_002", "acc_002", "Lunch", "Chipotle", 12.0, datetime(2026, 1, 24),
         "FOOD_AND_DRINK", "FOOD_AND_DRINK_LUNCH", "LOW", True, "USD", None),
    ]
)
def test_get_transactions(plaid_sandbox, txn_id, acc_id, name, merchant, amount, date_val,
                          primary, detailed, confidence, pending, iso_code, unofficial_code):

    mock_txn = MockPlaidTransaction(
        transaction_id=txn_id,
        account_id=acc_id,
        name=name,
        merchant_name=merchant,
        amount=amount,
        date=date_val,
        pending=pending,
        iso_currency_code=iso_code,
        unofficial_currency_code=unofficial_code,
        personal_finance_category=MockPersonalFinanceCategory(
            primary=primary,
            detailed=detailed,
            confidence_level=confidence
        ) if primary or detailed or confidence else None
    )

    plaid_sandbox.client.transactions_get = lambda req: type("Resp", (), {"transactions": [mock_txn]})()
    transactions = plaid_sandbox.get_transactions("access_token_123", date(2026,1,1), date(2026,1,31))

    assert len(transactions) == 1
    txn = transactions[0]
    assert isinstance(txn, Transaction)
    assert txn.transaction_id == txn_id
    assert txn.account_id == acc_id
    assert txn.name == name
    assert txn.merchant_name == merchant
    assert float(txn.amount) == amount
    assert txn.date == date_val
    assert txn.category_primary == primary
    assert txn.category_detailed == detailed
    assert txn.category_confidence_level == confidence
    assert txn.pending is pending
    assert txn.iso_currency_code == iso_code
    assert txn.unofficial_currency_code == unofficial_code
