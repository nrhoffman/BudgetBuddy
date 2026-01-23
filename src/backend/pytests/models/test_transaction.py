import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError
from app.models.transaction import Transaction

# -----------------------
# Parametrize valid transactions with different optional fields
# -----------------------
@pytest.mark.parametrize(
    "txn_data, expected_name, expected_merchant, expected_category, expected_pending, expected_iso",
    [
        (
            {
                "id": "txn_001",
                "account_id": "acc_001",
                "amount": Decimal("100.50"),
                "date": datetime(2026, 1, 23, 12, 0),
                "name": "Payment",
                "merchant_name": "Amazon",
                "category": ["Shopping", "Online"],
                "pending": False,
                "iso_currency_code": "USD"
            },
            "Payment", "Amazon", ["Shopping", "Online"], False, "USD"
        ),
        (
            {
                "id": "txn_002",
                "account_id": "acc_002",
                "amount": Decimal("50.25"),
                "date": datetime(2026, 1, 23, 12, 0),
            },
            None, None, None, None, None
        ),
        (
            {
                "id": "txn_003",
                "account_id": "acc_003",
                "amount": Decimal("10.00"),
                "date": datetime(2026, 1, 23, 12, 0),
                "name": "Subscription",
            },
            "Subscription", None, None, None, None
        )
    ]
)
def test_transaction_valid(txn_data, expected_name, expected_merchant, expected_category, expected_pending, expected_iso):
    txn = Transaction(**txn_data)
    assert txn.transaction_id == txn_data["id"]
    assert txn.account_id == txn_data["account_id"]
    assert txn.amount == txn_data["amount"]
    assert txn.date == txn_data["date"]

    assert txn.name == expected_name
    assert txn.merchant_name == expected_merchant
    assert txn.category == expected_category
    assert txn.pending == expected_pending
    assert txn.iso_currency_code == expected_iso
    assert txn.unofficial_currency_code is None


# -----------------------
# Parametrize invalid amounts
# -----------------------
@pytest.mark.parametrize("invalid_amount", [Decimal("0"), Decimal("0.00")])
def test_transaction_invalid_amounts(invalid_amount):
    with pytest.raises(ValidationError) as exc_info:
        Transaction(
            id="txn_invalid",
            account_id="acc_123",
            amount=invalid_amount,
            date=datetime(2026, 1, 23, 12, 0)
        )
    assert "Transaction amount cannot be zero" in str(exc_info.value)


# -----------------------
# Parametrize multiple alias values
# -----------------------
@pytest.mark.parametrize("txn_id", ["txn_alias_1", "txn_alias_2", "txn_alias_3"])
def test_transaction_alias_population(txn_id):
    txn = Transaction(
        id=txn_id,
        account_id="acc_alias",
        amount=Decimal("25.50"),
        date=datetime(2026, 1, 23, 12, 0)
    )
    assert txn.transaction_id == txn_id
