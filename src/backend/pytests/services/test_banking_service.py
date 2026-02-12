import pytest
from unittest.mock import Mock
from enum import Enum
from types import SimpleNamespace
from datetime import datetime

from app.services.banking_service import BankingService
from app.services.account_service import AccountService
from app.repositories.account_repository import AccountRepository
from app.repositories.bank_repository import BankRepository
from app.interfaces.banking_provider import BankingProvider
from app.models.banking_service_deps import BankingServiceDependencies
from app.exceptions import ConflictError, ExternalServiceError, ValidationError

# ---------------------------
# Fixtures
# ---------------------------
@pytest.fixture
def account_service_mock():
    return Mock(spec=AccountService)

@pytest.fixture
def account_repo_mock():
    return Mock(spec=AccountRepository)

@pytest.fixture
def bank_repo_mock():
    return Mock(spec=BankRepository)

@pytest.fixture
def banking_provider_mock():
    provider = Mock(spec=BankingProvider)
    provider.create_link_token.return_value = {"link_token": "mock-token"}
    provider.exchange_public_token.return_value = SimpleNamespace(
        access_token="access-token", item_id="item-123"
    )
    provider.get_accounts.return_value = None
    provider.get_transactions_sync.return_value = {"next_cursor": "cursor-123"}
    return provider

@pytest.fixture
def banking_service_deps(account_service_mock, account_repo_mock, bank_repo_mock, banking_provider_mock):
    return BankingServiceDependencies(
        account_service=account_service_mock,
        account_repo=account_repo_mock,
        bank_repo=bank_repo_mock,
        raw_provider_repo=Mock(),
        banking_provider=banking_provider_mock,
    )

@pytest.fixture
def banking_service(banking_service_deps):
    return BankingService(banking_service_deps)

# ---------------------------
# Mock objects
# ---------------------------
class MockBalances:
    def __init__(self, current=100):
        self.current = current

class MockAccountType(Enum):
    DEPOSITORY = "depository"
    CREDIT = "credit"

class MockTransactionObj:
    def __init__(
        self,
        account_id,
        amount=50,
        date=None,
        transaction_id=None,
        name="Mock Txn",
        merchant_name="Mock Merchant",
        pending=False,
        iso_currency_code="USD",
        unofficial_currency_code=None,
        personal_finance_category=None
    ):
        self.account_id = account_id
        self.amount = amount
        self.date = date or datetime.today().date()
        self.transaction_id = transaction_id or f"txn-{account_id}"
        self.name = name
        self.merchant_name = merchant_name
        self.pending = pending
        self.iso_currency_code = iso_currency_code
        self.unofficial_currency_code = unofficial_currency_code
        self.personal_finance_category = personal_finance_category

class MockTransactionsRes:
    def __init__(self, transactions):
        self.transactions = transactions
    def to_dict(self):
        return {"transactions": [t.transaction_id for t in self.transactions]}

class MockAccountObj:
    def __init__(self, account_id, name="Mock Account", type_=MockAccountType.DEPOSITORY, subtype="checking"):
        self.account_id = account_id
        self.id = account_id  # Added id property
        self.name = name
        self.type = type_
        self.subtype = subtype
        self.balances = MockBalances()

class MockAccountsRes:
    def __init__(self, accounts):
        self.accounts = accounts
    def to_dict(self):
        return {"accounts": [a.account_id for a in self.accounts]}

# ---------------------------
# Tests: create_bank_link_token
# ---------------------------
def test_create_bank_link_token_success(banking_service, banking_provider_mock):
    token = banking_service.create_bank_link_token("user-1")
    assert token == {"link_token": "mock-token"}
    banking_provider_mock.create_link_token.assert_called_once_with("user-1")

def test_create_bank_link_token_no_provider(account_service_mock, account_repo_mock, bank_repo_mock):
    deps = BankingServiceDependencies(
        account_service=account_service_mock,
        account_repo=account_repo_mock,
        bank_repo=bank_repo_mock,
        raw_provider_repo=Mock(),
        banking_provider=None,
    )
    service = BankingService(deps)
    with pytest.raises(ExternalServiceError):
        service.create_bank_link_token("user-1")

# ---------------------------
# Tests: add_bank_institution
# ---------------------------
@pytest.mark.parametrize("token_exists", [True, False])
def test_add_bank_institution_conflict_or_success(
    banking_service, bank_repo_mock, account_service_mock, banking_provider_mock, token_exists
):
    if token_exists:
        bank_repo_mock.get_by_user.return_value = SimpleNamespace(item_id="item-123")
        with pytest.raises(ConflictError):
            banking_service.add_bank_institution("user-1", "token", "inst-1")
    else:
        bank_repo_mock.get_by_user.return_value = None

        accounts = [MockAccountObj("acct1")]
        banking_provider_mock.get_accounts.return_value = MockAccountsRes(accounts)
        banking_provider_mock.get_transactions_sync.return_value = {"next_cursor": "cursor-123"}

        transactions = MockTransactionsRes([MockTransactionObj("acct1")])
        banking_service.get_transactions_within_dates = lambda token: transactions

        banking_service.banking_deps.raw_provider_repo.save = Mock()

        banking_service.add_bank_institution("user-1", "public-token", "inst-1", "Bank A")

        # Assert that the created account matches the expected id
        account_service_mock.create_account.assert_called_once()
        created_account = account_service_mock.create_account.call_args[0][0]
        assert created_account.id == accounts[0].account_id
        assert account_service_mock.create_account.call_args[0][1] == "user-1"

        account_service_mock.apply_transaction_changes.assert_called_once()

def test_add_bank_institution_provider_error(banking_service, bank_repo_mock, banking_provider_mock):
    bank_repo_mock.get_by_user.return_value = None
    banking_provider_mock.exchange_public_token.side_effect = Exception("fail")
    with pytest.raises(ExternalServiceError):
        banking_service.add_bank_institution("user-1", "token", "inst-1")

# ---------------------------
# Tests: add_bank_accounts
# ---------------------------
@pytest.mark.parametrize("existing_accounts,new_accounts,expected_created", [
    ([MockAccountObj("acct1")], [MockAccountObj("acct1"), MockAccountObj("acct2")], 1),
    ([MockAccountObj("acct1")], [MockAccountObj("acct1")], 0),
])
def test_add_bank_accounts_existing_and_new(
    banking_service, bank_repo_mock, account_repo_mock, account_service_mock, banking_provider_mock,
    existing_accounts, new_accounts, expected_created
):
    # Mock token from bank_repo
    token = SimpleNamespace(access_token="token", item_id="item-123")
    bank_repo_mock.get_by_user.return_value = token

    # Existing accounts in DB
    account_repo_mock.get_all_accounts_with_transactions.return_value = existing_accounts

    # New accounts from provider
    banking_provider_mock.get_accounts.return_value = MockAccountsRes(new_accounts)

    # Mock transactions object
    class MockTxnsRes:
        def __init__(self, transactions):
            self.transactions = transactions
        def to_dict(self):
            return {"transactions": [t.transaction_id for t in self.transactions]}

    # Only include transactions for accounts that will be created
    accounts_to_create_ids = {acc.account_id for acc in new_accounts} - {acc.account_id for acc in existing_accounts}
    mock_transactions = [MockTransactionObj(acc_id) for acc_id in accounts_to_create_ids]

    banking_service.get_transactions_within_dates = lambda access_token: MockTxnsRes(mock_transactions)

    # Mock raw_provider_repo.save to do nothing
    banking_service.banking_deps.raw_provider_repo.save = Mock()
    account_service_mock.reset_mock()

    # Run the method
    created_count = banking_service.add_bank_accounts("user-1")
    assert created_count == expected_created

    if expected_created > 0:
        # check that created accounts have correct ids
        for call_args in account_service_mock.create_account.call_args_list:
            created_account = call_args[0][0]
            assert created_account.id in [acc.account_id for acc in new_accounts]
        account_service_mock.apply_transaction_changes.assert_called()

def test_add_bank_accounts_no_token(banking_service, bank_repo_mock):
    bank_repo_mock.get_by_user.return_value = None
    with pytest.raises(ValidationError):
        banking_service.add_bank_accounts("user-1", "inst-1")

# ---------------------------
# Tests: plaid_webhook
# ---------------------------
def test_plaid_webhook_ignored(banking_service):
    payload = {"webhook_type": "OTHER", "webhook_code": "SYNC_UPDATES_AVAILABLE", "item_id": "item1"}
    result = banking_service.plaid_webhook(payload)
    assert result is None

def test_plaid_webhook_triggers_sync(banking_service, monkeypatch):
    payload = {"webhook_type": "TRANSACTIONS", "webhook_code": "SYNC_UPDATES_AVAILABLE", "item_id": "item1"}
    monkeypatch.setattr(banking_service, "enqueue_plaid_sync", lambda item_id: "queued")
    result = banking_service.plaid_webhook(payload)
    assert result is None

# ---------------------------
# Tests: get_transactions_within_dates
# ---------------------------
def test_get_transactions_within_dates_success(banking_service, banking_provider_mock):
    banking_provider_mock.get_transactions.return_value = ["tx1"]
    result = banking_service.get_transactions_within_dates("token")
    assert result == ["tx1"]

def test_get_transactions_within_dates_provider_error(banking_service, banking_provider_mock):
    banking_provider_mock.get_transactions.side_effect = Exception("fail")
    with pytest.raises(ExternalServiceError):
        banking_service.get_transactions_within_dates("token")
