import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from datetime import date

from app.services.banking_service import BankingService
from app.services.account_service import AccountService

# -------------------------------
# Sample data
# -------------------------------
class DummyAccount:
    def __init__(self, id, name="Checking"):
        self.id = id
        self.name = name

class DummyTransaction:
    def __init__(self, transaction_id, amount=50.0):
        self.transaction_id = transaction_id
        self.amount = amount

SAMPLE_ACCOUNT = DummyAccount("acc_1")
SAMPLE_TRANSACTION = DummyTransaction("txn_1")

# -------------------------------
# Fixtures
# -------------------------------
@pytest.fixture
def mock_account_service():
    return MagicMock(spec=AccountService)

@pytest.fixture
def mock_banking_provider():
    return MagicMock()

@pytest.fixture
def banking_service(mock_account_service, mock_banking_provider):
    return BankingService(account_service=mock_account_service,
                          banking_provider=mock_banking_provider)

# -------------------------------
# Tests for create_bank_link_token
# -------------------------------
def test_create_bank_link_token_success(banking_service, mock_banking_provider):
    mock_banking_provider.create_link_token.return_value = {"link_token": "token123"}

    result = banking_service.create_bank_link_token("user_1")
    assert result["link_token"] == "token123"
    mock_banking_provider.create_link_token.assert_called_once_with("user_1")

def test_create_bank_link_token_no_provider(mock_account_service):
    service = BankingService(account_service=mock_account_service, banking_provider=None)
    with pytest.raises(HTTPException) as e:
        service.create_bank_link_token("user_1")
    assert e.value.status_code == 500
    assert "Banking provider not configured" in e.value.detail

# -------------------------------
# Tests for add_bank_accounts
# -------------------------------
def test_add_bank_accounts_success(banking_service, mock_banking_provider, mock_account_service):
    # BankingProvider mocks
    mock_banking_provider.exchange_public_token.return_value = "access_123"
    mock_banking_provider.get_accounts.return_value = [SAMPLE_ACCOUNT]
    mock_banking_provider.get_transactions.return_value = [SAMPLE_TRANSACTION]

    result = banking_service.add_bank_accounts("user_1", "public_abc")
    assert result["status"] == "linked"
    assert result["accounts_added"] == 1

    mock_banking_provider.exchange_public_token.assert_called_once_with("public_abc")
    mock_banking_provider.get_accounts.assert_called_once_with("access_123")
    mock_account_service.create_account.assert_called_once_with(SAMPLE_ACCOUNT, "user_1")
    mock_account_service.add_transaction.assert_called_once_with("user_1", SAMPLE_ACCOUNT.id, SAMPLE_TRANSACTION)

def test_add_bank_accounts_no_provider(mock_account_service):
    service = BankingService(account_service=mock_account_service, banking_provider=None)
    with pytest.raises(HTTPException) as e:
        service.add_bank_accounts("user_1", "public_abc")
    assert e.value.status_code == 500
    assert "Banking provider not configured" in e.value.detail

def test_add_bank_accounts_provider_exception(banking_service, mock_banking_provider):
    mock_banking_provider.exchange_public_token.side_effect = Exception("provider error")

    with pytest.raises(HTTPException) as e:
        banking_service.add_bank_accounts("user_1", "public_abc")
    assert e.value.status_code == 500
    assert "Failed to link bank accounts" in e.value.detail
