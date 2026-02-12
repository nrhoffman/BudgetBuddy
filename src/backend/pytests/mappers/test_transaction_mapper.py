import pytest
from datetime import date, datetime
from types import SimpleNamespace
from app.models.transaction import Transaction
from app.models.account import AccountType
from app.mappers.transaction_mapper import sort_transactions, map_plaid_transaction

# ---------------------------
# Fixtures for test data
# ---------------------------

@pytest.fixture
def sample_transactions():
    """Return a small list of transactions with mixed dates and IDs."""
    return [
        Transaction(
            transaction_id="txn_2",
            account_id="acc_1",
            account_type=AccountType.DEPOSITORY,
            name="Coffee Shop",
            merchant_name="Starbucks",
            amount=5.0,
            date=date(2026, 2, 1),
        ),
        Transaction(
            transaction_id="txn_1",
            account_id="acc_2",
            account_type=AccountType.CREDIT,
            name="Bookstore",
            merchant_name="Barnes & Noble",
            amount=20.0,
            date=date(2026, 1, 31),
        ),
        Transaction(
            transaction_id="txn_3",
            account_id="acc_1",
            account_type=AccountType.DEPOSITORY,
            name="Grocery",
            merchant_name="Whole Foods",
            amount=50.0,
            date=date(2026, 2, 1),
        ),
    ]

@pytest.fixture
def plaid_txn_minimal():
    """Plaid transaction with only required fields."""
    return SimpleNamespace(
        transaction_id="txn_100",
        account_id="acc_99",
        name="Amazon",
        amount=100.0,
        date=date(2026, 2, 10),
    )

@pytest.fixture
def plaid_txn_full():
    pfc = SimpleNamespace(primary="Shops", detailed="Bookstore", confidence_level=0.9)  # float is fine now
    return SimpleNamespace(
        transaction_id="txn_101",
        account_id="acc_100",
        name="Barnes & Noble",
        merchant_name="Barnes & Noble",
        amount=25.0,
        date=date(2026, 2, 5),
        pending=True,
        iso_currency_code="USD",
        unofficial_currency_code=None,
        personal_finance_category=pfc
    )

# ---------------------------
# Tests for sort_transactions
# ---------------------------

def test_sort_transactions_deterministic(sample_transactions):
    """sort_transactions should sort by date then transaction_id."""
    sorted_txns = sort_transactions(sample_transactions)
    # Expected order: txn_1 (earliest), txn_2, txn_3 (same date, sorted by ID)
    assert [t.transaction_id for t in sorted_txns] == ["txn_1", "txn_2", "txn_3"]

def test_sort_transactions_empty_list():
    """sort_transactions should handle empty list without error."""
    assert sort_transactions([]) == []

def test_sort_transactions_single_item():
    """sort_transactions should handle single-item list."""
    txn = Transaction(
        transaction_id="txn_single",
        account_id="acc_1",
        account_type=AccountType.DEPOSITORY,
        name="Solo",
        merchant_name=None,
        amount=10.0,
        date=date(2026, 2, 10)
    )
    assert sort_transactions([txn]) == [txn]

# ---------------------------
# Tests for map_plaid_transaction
# ---------------------------

@pytest.mark.parametrize(
    "plaid_txn,account_type,expected_attrs",
    [
        (
            "plaid_txn_minimal",
            AccountType.DEPOSITORY,
            {
                "transaction_id": "txn_100",
                "account_id": "acc_99",
                "account_type": AccountType.DEPOSITORY,
                "name": "Amazon",
                "merchant_name": None,
                "amount": 100.0,
                # Use datetime.datetime to match Transaction model
                "date": datetime(2026, 2, 10),
                "category_primary": None,
                "category_detailed": None,
                "category_confidence_level": None,
                "pending": None,
                "iso_currency_code": None,
                "unofficial_currency_code": None,
            }
        ),
        (
            "plaid_txn_full",
            AccountType.CREDIT,
            {
                "transaction_id": "txn_101",
                "account_id": "acc_100",
                "account_type": AccountType.CREDIT,
                "name": "Barnes & Noble",
                "merchant_name": "Barnes & Noble",
                "amount": 25.0,
                # Use datetime.datetime to match Transaction model
                "date": datetime(2026, 2, 5),
                "category_primary": "Shops",
                "category_detailed": "Bookstore",
                # string type to match Transaction model
                "category_confidence_level": "0.9",
                "pending": True,
                "iso_currency_code": "USD",
                "unofficial_currency_code": None,
            }
        ),
    ],
)
def test_map_plaid_transaction(plaid_txn, account_type, expected_attrs, request):
    txn_obj = request.getfixturevalue(plaid_txn)
    mapped_txn = map_plaid_transaction(txn_obj, account_type)
    for attr, expected in expected_attrs.items():
        assert getattr(mapped_txn, attr) == expected

# ---------------------------
# Edge case: Plaid txn with missing personal_finance_category
# ---------------------------

def test_map_plaid_transaction_missing_pfc():
    txn = SimpleNamespace(
        transaction_id="txn_102",
        account_id="acc_101",
        name="Cafe",
        amount=12.0,
        date=date(2026, 2, 12),
    )
    mapped_txn = map_plaid_transaction(txn, AccountType.DEPOSITORY)
    assert mapped_txn.category_primary is None
    assert mapped_txn.category_detailed is None
    assert mapped_txn.category_confidence_level is None
