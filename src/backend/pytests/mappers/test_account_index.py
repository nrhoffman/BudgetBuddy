import pytest
from app.models.account import Account, AccountType
from app.mappers.account_index import AccountIndex

@pytest.fixture
def sample_accounts():
    return [
        Account(
            id="acc_1",
            type=AccountType.DEPOSITORY,
            name="Checking Account",
            subtype="checking",  # ✅ valid
            balance=1000.0
        ),
        Account(
            id="acc_2",
            type=AccountType.INVESTMENT,
            name="Investment Account",
            subtype="other",  # ✅ valid generic subtype
            balance=5000.0
        ),
        Account(
            id="acc_3",
            type=AccountType.CREDIT,
            name="Credit Card",
            subtype="credit card",  # ✅ valid
            balance=-250.0
        ),
    ]


@pytest.mark.parametrize(
    "account_id,expected_type",
    [
        ("acc_1", AccountType.DEPOSITORY),
        ("acc_2", AccountType.INVESTMENT),
        ("acc_3", AccountType.CREDIT),
    ],
)
def test_type_for_returns_correct_type(sample_accounts, account_id, expected_type):
    """AccountIndex.type_for returns the correct AccountType."""
    index = AccountIndex(sample_accounts)
    assert index.type_for(account_id) == expected_type


def test_type_for_raises_keyerror_for_unknown_account(sample_accounts):
    """AccountIndex.type_for raises KeyError for unknown account IDs."""
    index = AccountIndex(sample_accounts)
    with pytest.raises(KeyError):
        index.type_for("unknown_acc")


def test_init_creates_index_correctly(sample_accounts):
    """AccountIndex creates internal mapping correctly."""
    index = AccountIndex(sample_accounts)
    for acc in sample_accounts:
        assert index._by_id[acc.id] == acc


def test_init_with_duplicate_ids_raises_valueerror():
    accounts = [
        Account(id="acc_1", type=AccountType.DEPOSITORY, name="Checking", subtype="checking", balance=100),
        Account(id="acc_1", type=AccountType.INVESTMENT, name="Brokerage", subtype="other", balance=500),
    ]
    with pytest.raises(ValueError):
        AccountIndex(accounts)
