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
@pytest.mark.parametrize(
    "provider_configured, expected_exception, expected_token",
    [
        (True, None, {"link_token": "mock-token"}),
        (False, HTTPException, None),
    ]
)
def test_create_bank_link_token(banking_service, account_service_mock, account_repo_mock, bank_repo_mock,
                                banking_provider_mock, provider_configured, expected_exception, expected_token):
    service = banking_service if provider_configured else BankingService(
        account_service_mock, account_repo_mock, bank_repo_mock, banking_provider=None
    )
    if expected_exception:
        with pytest.raises(expected_exception) as exc:
            service.create_bank_link_token("user-1")
        assert exc.value.status_code == 500
    else:
        token = service.create_bank_link_token("user-1")
        assert token == expected_token
        banking_provider_mock.create_link_token.assert_called_once_with("user-1")


# ---------------------------
# add_bank_institution
# ---------------------------
@pytest.mark.parametrize(
    "existing_token, accounts, transactions, expected_status, accounts_added",
    [
        (Mock(item_id="item-123"), [], [], "already_linked", None),
        (None, [], [], "linked", 0),
        (None, ["acct1"], ["tx1"], "linked", 1),
    ]
)
def test_add_bank_institution(banking_service, bank_repo_mock, account_service_mock,
                              banking_provider_mock, existing_token, accounts, transactions,
                              expected_status, accounts_added):
    # Setup bank repo
    bank_repo_mock.get_by_user.return_value = existing_token

    # Setup accounts & transactions
    class MockAccount:
        def __init__(self, id):
            self.id = id

    class MockTransaction:
        def __init__(self, account_id):
            self.account_id = account_id

    banking_provider_mock.get_accounts.return_value = [MockAccount(a) for a in accounts]
    banking_provider_mock.get_transactions.return_value = [MockTransaction("acct1") for a in transactions]

    # Patch get_transactions_within_dates to return transactions
    banking_service.get_transactions_within_dates = lambda access_token: [MockTransaction("acct1") for a in transactions]

    if existing_token:
        result = banking_service.add_bank_institution("user-1", "token", "inst-1", "Bank A")
        assert result["status"] == expected_status
        assert result["item_id"] == existing_token.item_id
    else:
        result = banking_service.add_bank_institution("user-1", "token", "inst-1", "Bank A")
        assert result["status"] == expected_status
        assert result.get("accounts_added") == accounts_added
        if accounts_added:
            account_service_mock.create_account.assert_called()
            account_service_mock.apply_transaction_changes.assert_called()


def test_add_bank_institution_exception(banking_service, bank_repo_mock, banking_provider_mock):
    banking_provider_mock.exchange_public_token.side_effect = Exception("fail")
    with pytest.raises(HTTPException) as exc:
        banking_service.add_bank_institution("user-1", "token", "inst-1", "Bank A")
    assert exc.value.status_code == 500
    assert "Failed to link bank accounts" in exc.value.detail


# ---------------------------
# add_bank_accounts (sync)
# ---------------------------
@pytest.mark.parametrize(
    "token_exists, accounts_existing, accounts_new, expected_status, accounts_added",
    [
        (False, [], [], RuntimeError, None),  # No token
        (True, ["acct-1"], ["acct-1"], "linked", 0),  # No new accounts
        (True, [], ["acct-1"], "linked", 1),  # One new account
    ]
)
def test_add_bank_accounts(banking_service, bank_repo_mock, account_repo_mock, account_service_mock,
                           banking_provider_mock, token_exists, accounts_existing, accounts_new,
                           expected_status, accounts_added):
    class MockAccount:
        def __init__(self, id):
            self.id = id

    class MockTransaction:
        def __init__(self, account_id):
            self.account_id = account_id

    bank_repo_mock.get_by_user.return_value = Mock(access_token="token", item_id="item-123") if token_exists else None
    banking_provider_mock.get_accounts.return_value = [MockAccount(a) for a in accounts_new]
    account_repo_mock.get_all_accounts_with_transactions.return_value = [MockAccount(a) for a in accounts_existing]
    banking_service.get_transactions_within_dates = lambda token: [MockTransaction("acct-1")]

    if not token_exists:
        with pytest.raises(expected_status):
            banking_service.add_bank_accounts("user-1", "inst-1")
    else:
        # Fix: patch get_transactions_within_dates properly
        banking_service.get_transactions_within_dates = lambda access_token: [MockTransaction("acct-1")]
        result = banking_service.add_bank_accounts("user-1", "inst-1")
        assert result["status"] == expected_status
        assert result["accounts_added"] == accounts_added


# ---------------------------
# plaid_webhook
# ---------------------------
@pytest.mark.parametrize(
    "payload, expected_status",
    [
        ({"webhook_type": "OTHER", "webhook_code": "SYNC_UPDATES_AVAILABLE", "item_id": "item1"}, "ignored"),
        ({"webhook_type": "TRANSACTIONS", "webhook_code": "OTHER_CODE", "item_id": "item1"}, "ignored"),
        ({"webhook_type": "TRANSACTIONS", "webhook_code": "SYNC_UPDATES_AVAILABLE", "item_id": "item1"}, "ok"),
        ({"webhook_type": "TRANSACTIONS", "webhook_code": "INITIAL_UPDATE", "item_id": "item2"}, "ok"),
    ]
)
def test_plaid_webhook(banking_service, payload, expected_status, monkeypatch):
    if expected_status == "ok":
        monkeypatch.setattr(banking_service, "enqueue_plaid_sync", lambda item_id: None)
    result = banking_service.plaid_webhook(payload)
    assert result["status"] == expected_status


# ---------------------------
# get_transactions_within_dates
# ---------------------------
def test_get_transactions_within_dates_success(banking_service, banking_provider_mock):
    banking_provider_mock.get_transactions.return_value = ["tx1"]
    result = banking_service.get_transactions_within_dates("token")
    assert result == ["tx1"]
    banking_provider_mock.get_transactions.assert_called_once()


def test_get_transactions_within_dates_failure(banking_service, banking_provider_mock):
    banking_provider_mock.get_transactions.side_effect = Exception("fail")
    with pytest.raises(RuntimeError) as exc:
        banking_service.get_transactions_within_dates("token")
    assert "Error fetching transactions" in str(exc.value)
