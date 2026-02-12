import pytest
from types import SimpleNamespace
from app.models.plaid_task_context import PlaidTaskContext

# ---------------------------
# Fixtures for dummy dependencies
# ---------------------------

@pytest.fixture
def dummy_db():
    return SimpleNamespace(name="DBSessionDummy")

@pytest.fixture
def dummy_bank_repo():
    return SimpleNamespace(name="BankRepoDummy")

@pytest.fixture
def dummy_account_repo():
    return SimpleNamespace(name="AccountRepoDummy")

@pytest.fixture
def dummy_txn_repo():
    return SimpleNamespace(name="TxnRepoDummy")

@pytest.fixture
def dummy_raw_provider_repo():
    return SimpleNamespace(name="RawProviderRepoDummy")

@pytest.fixture
def dummy_account_service():
    return SimpleNamespace(name="AccountServiceDummy")

@pytest.fixture
def dummy_plaid():
    return SimpleNamespace(name="PlaidSandboxDummy")


# ---------------------------
# Parametrized tests for initialization
# ---------------------------

@pytest.mark.parametrize(
    "db, bank_repo, account_repo, txn_repo, raw_provider_repo, account_service, plaid",
    [
        ("dummy_db", "dummy_bank_repo", "dummy_account_repo", "dummy_txn_repo", "dummy_raw_provider_repo", "dummy_account_service", "dummy_plaid"),
    ]
)
def test_plaid_task_context_init(db, bank_repo, account_repo, txn_repo, raw_provider_repo, account_service, plaid, request):
    """
    Test that PlaidTaskContext correctly initializes with all dependencies.
    """
    # Get actual fixture objects
    db_obj = request.getfixturevalue(db)
    bank_repo_obj = request.getfixturevalue(bank_repo)
    account_repo_obj = request.getfixturevalue(account_repo)
    txn_repo_obj = request.getfixturevalue(txn_repo)
    raw_provider_repo_obj = request.getfixturevalue(raw_provider_repo)
    account_service_obj = request.getfixturevalue(account_service)
    plaid_obj = request.getfixturevalue(plaid)

    context = PlaidTaskContext(
        db=db_obj,
        bank_repo=bank_repo_obj,
        account_repo=account_repo_obj,
        txn_repo=txn_repo_obj,
        raw_provider_repo=raw_provider_repo_obj,
        account_service=account_service_obj,
        plaid=plaid_obj,
    )

    # Assert all attributes are correctly assigned
    assert context.db == db_obj
    assert context.bank_repo == bank_repo_obj
    assert context.account_repo == account_repo_obj
    assert context.txn_repo == txn_repo_obj
    assert context.raw_provider_repo == raw_provider_repo_obj
    assert context.account_service == account_service_obj
    assert context.plaid == plaid_obj


# ---------------------------
# Test dataclass __repr__ for coverage
# ---------------------------

def test_plaid_task_context_repr(dummy_db, dummy_bank_repo, dummy_account_repo,
                                dummy_txn_repo, dummy_raw_provider_repo,
                                dummy_account_service, dummy_plaid):
    context = PlaidTaskContext(
        db=dummy_db,
        bank_repo=dummy_bank_repo,
        account_repo=dummy_account_repo,
        txn_repo=dummy_txn_repo,
        raw_provider_repo=dummy_raw_provider_repo,
        account_service=dummy_account_service,
        plaid=dummy_plaid,
    )

    repr_str = repr(context)
    assert "PlaidTaskContext" in repr_str
    assert "db" in repr_str
    assert "bank_repo" in repr_str
    assert "account_repo" in repr_str
    assert "txn_repo" in repr_str
    assert "raw_provider_repo" in repr_str
    assert "account_service" in repr_str
    assert "plaid" in repr_str
