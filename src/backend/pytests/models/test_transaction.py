"""
Parametrized pytest for Transaction and UpdateTransaction Pydantic models.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError
from app.models.transaction import Transaction, UpdateTransaction


# -----------------------
# Parametrized valid Transaction inputs
# -----------------------
@pytest.mark.parametrize(
    "txn_data, expected_name, expected_merchant, expected_primary, "
    "expected_detailed, expected_confidence, expected_pending, expected_iso",
    [
        (
            {
                "id": "txn_001",
                "account_id": "acc_001",
                "amount": Decimal("100.50"),
                "date": datetime(2026, 1, 23, 12, 0),
                "name": "Payment",
                "merchant_name": "Amazon",
                "category_primary": "SHOPPING",
                "category_detailed": "SHOPPING_ONLINE",
                "category_confidence_level": "HIGH",
                "pending": False,
                "iso_currency_code": "USD",
            },
            "Payment",
            "Amazon",
            "SHOPPING",
            "SHOPPING_ONLINE",
            "HIGH",
            False,
            "USD",
        ),
        (
            {
                "id": "txn_002",
                "account_id": "acc_002",
                "amount": Decimal("50.25"),
                "date": datetime(2026, 1, 23, 12, 0),
            },
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ),
        (
            {
                "id": "txn_003",
                "account_id": "acc_003",
                "amount": Decimal("10.00"),
                "date": datetime(2026, 1, 23, 12, 0),
                "name": "Subscription",
                "category_primary": "SERVICES",
            },
            "Subscription",
            None,
            "SERVICES",
            None,
            None,
            None,
            None,
        ),
    ],
)
def test_transaction_valid(
    txn_data,
    expected_name,
    expected_merchant,
    expected_primary,
    expected_detailed,
    expected_confidence,
    expected_pending,
    expected_iso,
):
    """Test creating valid Transaction instances with optional fields."""
    txn = Transaction(**txn_data)
    assert txn.transaction_id == txn_data["id"]
    assert txn.account_id == txn_data["account_id"]
    assert txn.amount == txn_data["amount"]
    assert txn.date == txn_data["date"]
    assert txn.name == expected_name
    assert txn.merchant_name == expected_merchant
    assert txn.category_primary == expected_primary
    assert txn.category_detailed == expected_detailed
    assert txn.category_confidence_level == expected_confidence
    assert txn.pending == expected_pending
    assert txn.iso_currency_code == expected_iso
    assert txn.unofficial_currency_code is None


# -----------------------
# Parametrized invalid Transaction amounts
# -----------------------
@pytest.mark.parametrize("invalid_amount", [Decimal("0"), Decimal("0.00")])
def test_transaction_invalid_amounts(invalid_amount):
    """Ensure creating a Transaction with zero amount raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        Transaction(
            id="txn_invalid",
            account_id="acc_123",
            amount=invalid_amount,
            date=datetime(2026, 1, 23, 12, 0),
        )
    assert "Transaction amount cannot be zero" in str(exc_info.value)


# -----------------------
# Parametrized alias testing
# -----------------------
@pytest.mark.parametrize("txn_id", ["txn_alias_1", "txn_alias_2", "txn_alias_3"])
def test_transaction_alias_population(txn_id):
    """Ensure Transaction ID alias populates transaction_id field."""
    txn = Transaction(
        id=txn_id,
        account_id="acc_alias",
        amount=Decimal("25.50"),
        date=datetime(2026, 1, 23, 12, 0),
    )
    assert txn.transaction_id == txn_id


# -----------------------
# Parametrized UpdateTransaction tests
# -----------------------
@pytest.mark.parametrize(
    "update_data, expected_primary, expected_detailed, expected_confidence",
    [
        ({"category_primary": "FOOD"}, "FOOD", None, "MANUAL"),
        ({"category_detailed": "GROCERIES"}, None, "GROCERIES", "MANUAL"),
        (
            {"category_primary": "SHOPPING", "category_detailed": "ONLINE",
             "category_confidence_level": "HIGH"},
            "SHOPPING",
            "ONLINE",
            "HIGH",
        ),
        ({}, None, None, "MANUAL"),
    ],
)
def test_update_transaction_valid(update_data, expected_primary,
                                  expected_detailed, expected_confidence):
    """Test creating UpdateTransaction instances with optional fields."""
    update_txn = UpdateTransaction(**update_data)
    assert update_txn.category_primary == expected_primary
    assert update_txn.category_detailed == expected_detailed
    assert update_txn.category_confidence_level == expected_confidence
