"""
Parametrized tests for Account domain model and parsing functions.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.models.account import (
    Account,
    AccountType,
    AccountSubType,
    parse_account_type,
    parse_account_subtype,
)


# -----------------------------
# Parametrized tests for AccountType parsing
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
    """Ensure parse_account_type returns the correct AccountType enum."""
    assert parse_account_type(input_value) == expected


# -----------------------------
# Parametrized tests for AccountSubType parsing
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
    """Ensure parse_account_subtype returns the correct AccountSubType enum."""
    assert parse_account_subtype(input_value) == expected


# -----------------------------
# Parametrized tests for Account model creation
# -----------------------------
@pytest.mark.parametrize(
    "account_id, name, type_, subtype, balance, transactions",
    [
        ("123", "My Checking", AccountType.DEPOSITORY, AccountSubType.CHECKING,
         Decimal("100.50"), []),
        ("456", "Savings Account", AccountType.DEPOSITORY, AccountSubType.SAVINGS,
         Decimal("500.00"), None),
        ("789", "Unknown Account", AccountType.OTHER, None, Decimal("0.00"), None),
    ],
)
def test_account_model(account_id, name, type_, subtype, balance, transactions):
    """Ensure Account model initializes correctly with various inputs."""
    account = Account(
        id=account_id,
        name=name,
        type=type_,
        subtype=subtype,
        balance=balance,
        transactions=transactions or [],
        initial_balance=balance,
        initial_import_completed_at=datetime.now(timezone.utc),
    )

    assert account.id == account_id
    assert account.name == name
    assert account.type == type_
    assert account.subtype == subtype
    assert account.balance == balance
    assert isinstance(account.transactions, list)
    if transactions is None:
        assert account.transactions == []
    else:
        assert account.transactions == transactions
