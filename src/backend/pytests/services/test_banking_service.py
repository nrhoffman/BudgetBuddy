import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from datetime import datetime, timedelta

from app.services.banking_service import BankingService
from app.services.account_service import AccountService
from app.repositories.account_repository import AccountRepository
from app.repositories.bank_repository import BankRepository
from app.interfaces.banking_provider import BankingProvider
from app.models.transaction import Transaction
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
    provider.exchange_public_token.return_value = Mock(
        access_token="access-token", item_id="item-123"
    )
    provider.get_accounts.return_value = []
    provider.get_transactions.return_value = []
    provider.get_transactions_sync.return_value = {"next_cursor": "cursor-123"}
    return provider


@pytest.fixture
def banking_service(account_service_mock, account_repo_mock, bank_repo_mock, banking_provider_mock):
    return BankingService(
        account_service=account_service_mock,
        account_repo=account_repo_mock,
        bank_repo=bank_repo_mock,
        banking_provider=banking_provider_mock,
    )


# ---------------------------
# create_bank_link_token
# ---------------------------
def test_create_bank_link_token_success(banking_service, banking_provider_mock):
    token = banking_service.create_bank_link_token("user-1")
    assert token == {"link_token": "mock-token"}
    banking_provider_mock.create_link_token.assert_called_once_with("user-1")


def test_create_bank_link_token_no_provider(account_service_mock, account_repo_mock, bank_repo_mock):
    service = BankingService(account_service_mock, account_repo_mock, bank_repo_mock, banking_provider=None)
    with pytest.raises(ExternalServiceError) as exc:
        service.create_bank_link_token("user-1")
    assert "Banking provider not configured" in str(exc.value)


# ---------------------------
# add_bank_institution
# ---------------------------
def test_add_bank_institution_conflict(banking_service, bank_repo_mock):
    bank_repo_mock.get_by_user.return_value = Mock(item_id="item-123")
    with pytest.raises(ConflictError):
        banking_service.add_bank_institution("user-1", "token", "inst-1")


def test_add_bank_institution_success(banking_service, bank_repo_mock, account_service_mock, banking_provider_mock):
    bank_repo_mock.get_by_user.return_value = None
    # Mock accounts and transactions returned from provider
    class MockAccount: 
        def __init__(self, id): self.id = id
    class MockTransaction:
        def __init__(self, account_id): self.account_id = account_id

    accounts = [MockAccount("acct1")]
    transactions = [MockTransaction("acct1")]
    banking_provider_mock.get_accounts.return_value = accounts
    banking_service.get_transactions_within_dates = lambda token: transactions

    banking_service.add_bank_institution("user-1", "public-token", "inst-1", "Bank A")

    account_service_mock.create_account.assert_called_once_with(accounts[0], "user-1")
    account_service_mock.apply_transaction_changes.assert_called_once()


def test_add_bank_institution_provider_error(banking_service, bank_repo_mock, banking_provider_mock):
    bank_repo_mock.get_by_user.return_value = None
    banking_provider_mock.exchange_public_token.side_effect = Exception("fail")
    with pytest.raises(ExternalServiceError) as exc:
        banking_service.add_bank_institution("user-1", "token", "inst-1")
    assert "Failed to link bank accounts" in str(exc.value)


# ---------------------------
# add_bank_accounts
# ---------------------------
def test_add_bank_accounts_no_token(banking_service, bank_repo_mock):
    bank_repo_mock.get_by_user.return_value = None
    with pytest.raises(ValidationError):
        banking_service.add_bank_accounts("user-1", "inst-1")


def test_add_bank_accounts_existing_and_new(banking_service, bank_repo_mock, account_repo_mock, account_service_mock, banking_provider_mock):
    class MockAccount:
        def __init__(self, id): self.id = id
    class MockTransaction:
        def __init__(self, account_id): self.account_id = account_id

    token = Mock(access_token="token", item_id="item-123")
    bank_repo_mock.get_by_user.return_value = token

    existing_accounts = [MockAccount("acct1")]
    account_repo_mock.get_all_accounts_with_transactions.return_value = existing_accounts

    new_accounts = [MockAccount("acct1"), MockAccount("acct2")]
    banking_provider_mock.get_accounts.return_value = new_accounts

    transactions = [MockTransaction("acct1"), MockTransaction("acct2")]
    banking_service.get_transactions_within_dates = lambda token: transactions

    created_count = banking_service.add_bank_accounts("user-1")
    assert created_count == 1
    account_service_mock.create_account.assert_called_once_with(new_accounts[1], "user-1")
    account_service_mock.apply_transaction_changes.assert_called_once()


# ---------------------------
# plaid_webhook
# ---------------------------
def test_plaid_webhook_ignored(banking_service):
    payload = {"webhook_type": "OTHER", "webhook_code": "SYNC_UPDATES_AVAILABLE", "item_id": "item1"}
    result = banking_service.plaid_webhook(payload)
    assert result is None  # Ignored events return nothing


def test_plaid_webhook_triggers_sync(banking_service, monkeypatch):
    payload = {"webhook_type": "TRANSACTIONS", "webhook_code": "SYNC_UPDATES_AVAILABLE", "item_id": "item1"}
    monkeypatch.setattr(banking_service, "enqueue_plaid_sync", lambda item_id: "queued")
    result = banking_service.plaid_webhook(payload)
    assert result is None  # Function itself returns nothing


# ---------------------------
# get_transactions_within_dates
# ---------------------------
def test_get_transactions_within_dates_success(banking_service, banking_provider_mock):
    banking_provider_mock.get_transactions.return_value = ["tx1"]
    result = banking_service.get_transactions_within_dates("token")
    assert result == ["tx1"]


def test_get_transactions_within_dates_provider_error(banking_service, banking_provider_mock):
    banking_provider_mock.get_transactions.side_effect = Exception("fail")
    with pytest.raises(ExternalServiceError):
        banking_service.get_transactions_within_dates("token")
