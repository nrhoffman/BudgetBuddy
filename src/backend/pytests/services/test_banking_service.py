import pytest
from unittest.mock import MagicMock
from datetime import datetime, date, timedelta
from decimal import Decimal
from fastapi import HTTPException

from app.services.banking_service import BankingService
from app.services.account_service import AccountService


# -------------------------------
# Sample data (provider-shaped)
# -------------------------------
class DummyAccount:
    def __init__(
        self,
        id,
        name="Checking",
        balance=1000.0,
        type="depository",
    ):
        self.id = id
        self.name = name
        self.balance = balance
        self.type = type


class DummyTransaction:
    def __init__(
        self,
        transaction_id,
        account_id,
        amount,
        date,
        category_primary="GENERAL",
    ):
        self.transaction_id = transaction_id
        self.account_id = account_id
        self.amount = Decimal(amount)
        self.date = date
        self.category_primary = category_primary


SAMPLE_ACCOUNT = DummyAccount(
    id="acc_1",
    balance=1000.0,
    type="depository",
)

SAMPLE_TRANSACTION = DummyTransaction(
    transaction_id="txn_1",
    account_id="acc_1",
    amount=50.0,
    date=datetime(2026, 1, 23),
    category_primary="GENERAL",
)


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
    return BankingService(
        account_service=mock_account_service,
        banking_provider=mock_banking_provider,
    )


# -------------------------------
# Tests for create_bank_link_token
# -------------------------------
def test_create_bank_link_token_success(
    banking_service,
    mock_banking_provider,
):
    mock_banking_provider.create_link_token.return_value = {
        "link_token": "token123"
    }

    result = banking_service.create_bank_link_token("user_1")

    assert result["link_token"] == "token123"
    mock_banking_provider.create_link_token.assert_called_once_with("user_1")


def test_create_bank_link_token_no_provider(mock_account_service):
    service = BankingService(
        account_service=mock_account_service,
        banking_provider=None,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_bank_link_token("user_1")

    assert exc.value.status_code == 500
    assert "Banking provider not configured" in exc.value.detail


# -------------------------------
# Tests for add_bank_accounts
# -------------------------------
def test_add_bank_accounts_success(
    banking_service,
    mock_banking_provider,
    mock_account_service,
):
    mock_banking_provider.exchange_public_token.return_value = "access_123"
    mock_banking_provider.get_accounts.return_value = [SAMPLE_ACCOUNT]
    mock_banking_provider.get_transactions.return_value = [SAMPLE_TRANSACTION]

    result = banking_service.add_bank_accounts("user_1", "public_abc")

    assert result == {
        "status": "linked",
        "accounts_added": 1,
    }

    mock_banking_provider.exchange_public_token.assert_called_once_with(
        "public_abc"
    )

    mock_banking_provider.get_accounts.assert_called_once_with(
        "access_123"
    )

    # Date range assertions
    call_args = mock_banking_provider.get_transactions.call_args
    assert call_args.args[0] == "access_123"

    start_date = call_args.args[1]
    end_date = call_args.args[2]

    assert isinstance(start_date, date)
    assert isinstance(end_date, date)
    assert (end_date - start_date).days == 90

    mock_account_service.create_account.assert_called_once_with(
        SAMPLE_ACCOUNT,
        "user_1",
    )

    mock_account_service.add_transaction.assert_called_once()
    args = mock_account_service.add_transaction.call_args.args

    assert args[0] == "user_1"
    assert args[1] == SAMPLE_ACCOUNT.id
    assert args[2].transaction_id == "txn_1"
    assert hasattr(args[2], "balance_after")


def test_add_bank_accounts_no_provider(mock_account_service):
    service = BankingService(
        account_service=mock_account_service,
        banking_provider=None,
    )

    with pytest.raises(HTTPException) as exc:
        service.add_bank_accounts("user_1", "public_abc")

    assert exc.value.status_code == 500
    assert "Banking provider not configured" in exc.value.detail


def test_add_bank_accounts_provider_exception(
    banking_service,
    mock_banking_provider,
):
    mock_banking_provider.exchange_public_token.side_effect = Exception(
        "provider error"
    )

    with pytest.raises(HTTPException) as exc:
        banking_service.add_bank_accounts("user_1", "public_abc")

    assert exc.value.status_code == 500
    assert "Failed to link bank accounts" in exc.value.detail
