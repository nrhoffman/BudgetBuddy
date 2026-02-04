import pytest
from unittest.mock import AsyncMock, Mock
from fastapi import HTTPException
from datetime import datetime, timedelta

from app.services.banking_service import BankingService
from app.services.account_service import AccountService
from app.repositories.account_repository import AccountRepository
from app.repositories.bank_repository import BankRepository
from app.interfaces.banking_provider import BankingProvider


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
def banking_service(
    account_service_mock,
    account_repo_mock,
    bank_repo_mock,
    banking_provider_mock,
):
    return BankingService(
        account_service=account_service_mock,
        account_repo=account_repo_mock,
        bank_repo=bank_repo_mock,
        banking_provider=banking_provider_mock,
    )


# ---------------------------
# create_bank_link_token tests
# ---------------------------
def test_create_bank_link_token_success(banking_service, banking_provider_mock):
    result = banking_service.create_bank_link_token("user-1")
    assert result == {"link_token": "mock-token"}
    banking_provider_mock.create_link_token.assert_called_once_with("user-1")


def test_create_bank_link_token_no_provider(account_service_mock, account_repo_mock, bank_repo_mock):
    service = BankingService(account_service_mock, account_repo_mock, bank_repo_mock, banking_provider=None)
    with pytest.raises(HTTPException) as exc:
        service.create_bank_link_token("user-1")
    assert exc.value.status_code == 500
    assert "Banking provider not configured" in exc.value.detail


# ---------------------------
# add_bank_accounts tests
# ---------------------------
def test_add_bank_accounts_already_linked(banking_service, bank_repo_mock, banking_provider_mock):
    bank_repo_mock.get_by_user.return_value = Mock(item_id="existing-item")
    result = banking_service.add_bank_accounts("user-1", "token", "inst-1", "Bank A")
    assert result["status"] == "already_linked"
    assert result["item_id"] == "existing-item"


def test_add_bank_accounts_no_accounts(banking_service, bank_repo_mock, banking_provider_mock):
    bank_repo_mock.get_by_user.return_value = None
    banking_provider_mock.get_accounts.return_value = []
    result = banking_service.add_bank_accounts("user-1", "token", "inst-1", "Bank A")
    assert result["status"] == "linked"
    assert result["accounts_added"] == 0


def test_add_bank_accounts_with_accounts(
    banking_service, bank_repo_mock, banking_provider_mock, account_service_mock
):
    bank_repo_mock.get_by_user.return_value = None

    class MockAccount:
        id = "acct-1"

    class MockTransaction:
        account_id = "acct-1"

    banking_provider_mock.get_accounts.return_value = [MockAccount()]
    banking_provider_mock.get_transactions.return_value = [MockTransaction()]
    result = banking_service.add_bank_accounts("user-1", "token", "inst-1", "Bank A")

    assert result["status"] == "linked"
    assert result["accounts_added"] == 1
    account_service_mock.create_account.assert_called_once()
    account_service_mock.apply_transaction_changes.assert_called_once()


def test_add_bank_accounts_exception(banking_service, bank_repo_mock, banking_provider_mock):
    banking_provider_mock.exchange_public_token.side_effect = Exception("fail")
    with pytest.raises(HTTPException) as exc:
        banking_service.add_bank_accounts("user-1", "token", "inst-1", "Bank A")
    assert exc.value.status_code == 500
    assert "Failed to link bank accounts" in exc.value.detail


# ---------------------------
# plaid_webhook tests
# ---------------------------
@pytest.mark.parametrize(
    "payload,expected_status",
    [
        ({"webhook_type": "OTHER", "webhook_code": "SYNC_UPDATES_AVAILABLE", "item_id": "item1"}, "ignored"),
        ({"webhook_type": "TRANSACTIONS", "webhook_code": "OTHER_CODE", "item_id": "item1"}, "ignored"),
        ({"webhook_type": "TRANSACTIONS", "webhook_code": "SYNC_UPDATES_AVAILABLE", "item_id": "item1"}, "ok"),
        ({"webhook_type": "TRANSACTIONS", "webhook_code": "INITIAL_UPDATE", "item_id": "item2"}, "ok"),
    ],
)
def test_plaid_webhook(banking_service, payload, expected_status, monkeypatch):
    if expected_status == "ok":
        # Patch enqueue_plaid_sync to avoid calling Celery task
        monkeypatch.setattr(banking_service, "enqueue_plaid_sync", lambda item_id: None)

    result = banking_service.plaid_webhook(payload)
    assert result["status"] == expected_status
