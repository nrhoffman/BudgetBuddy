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
    ]
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
        ("home equity", AccountSubType.HOMEEQUITY),
        ("line of credit", AccountSubType.LINEOFCREDIT),
        ("student", AccountSubType.STUDENT),
        ("auto", AccountSubType.AUTO),
        ("mortgage", AccountSubType.MORTGAGE),
        ("hsa", AccountSubType.HSA),
        ("invalid_subtype", AccountSubType.OTHER),
        ("", AccountSubType.OTHER),
    ]
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
        transactions=[]
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
        balance=Decimal("500.00")
    )
    assert account.transactions == []
