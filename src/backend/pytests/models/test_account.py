import pytest
from decimal import Decimal

from app.models.account import (
    Account,
    AccountType,
    AccountSubType,
    parse_account_type,
    parse_account_subtype,
)

# -----------------------------
# Tests for AccountType parsing
# -----------------------------
@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("depository", AccountType.DEPOSITORY),
        ("CREDIT", AccountType.CREDIT),
        (" brokerage ", AccountType.BROKERAGE),
        ("investment", AccountType.INVESTMENT),
        ("loan", AccountType.LOAN),
        ("random_invalid", AccountType.OTHER),
        ("", AccountType.OTHER),
        (None, AccountType.OTHER),
    ],
)
def test_parse_account_type(input_value, expected):
    assert parse_account_type(input_value) == expected


# -----------------------------
# Tests for AccountSubType parsing
# -----------------------------
@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("checking", AccountSubType.CHECKING),
        ("SAVINGS", AccountSubType.SAVINGS),
        ("money market", AccountSubType.MONEY_MARKET),
        ("cash management", AccountSubType.CASH_MANAGEMENT),
        ("cd", AccountSubType.CD),
        ("hsa", AccountSubType.HEALTH_SAVINGS),
        ("credit card", AccountSubType.CREDIT_CARD),
        ("auto", AccountSubType.AUTO_LOAN),
        ("student", AccountSubType.STUDENT_LOAN),
        ("mortgage", AccountSubType.MORTGAGE),
        ("line of credit", AccountSubType.LINE_OF_CREDIT),
        ("home equity", AccountSubType.HOME_EQUITY),
        ("ira", AccountSubType.IRA),
        ("401k", AccountSubType._401K),
        ("invalid_subtype", AccountSubType.OTHER),
        ("", AccountSubType.OTHER),
        (None, AccountSubType.OTHER),
    ],
)
def test_parse_account_subtype(input_value, expected):
    assert parse_account_subtype(input_value) == expected


# -----------------------------
# Tests for Account model
# -----------------------------
def test_account_model_creation():
    account = Account(
        id="123",
        name="My Checking",
        type=AccountType.DEPOSITORY,
        subtype=AccountSubType.CHECKING,
        balance=Decimal("100.50"),
        transactions=[],
    )

    assert account.id == "123"
    assert account.name == "My Checking"
    assert account.type == AccountType.DEPOSITORY
    assert account.subtype == AccountSubType.CHECKING
    assert account.balance == Decimal("100.50")
    assert isinstance(account.transactions, list)
    assert len(account.transactions) == 0


def test_account_model_default_transactions():
    """Ensure transactions default to an empty list if not provided."""
    account = Account(
        id="456",
        name="Savings Account",
        type=AccountType.DEPOSITORY,
        subtype=AccountSubType.SAVINGS,
        balance=Decimal("500.00"),
    )

    assert account.transactions == []


def test_account_model_allows_null_subtype():
    """Subtype is optional and may be None."""
    account = Account(
        id="789",
        name="Unknown Account",
        type=AccountType.OTHER,
        subtype=None,
        balance=Decimal("0.00"),
    )

    assert account.subtype is None
