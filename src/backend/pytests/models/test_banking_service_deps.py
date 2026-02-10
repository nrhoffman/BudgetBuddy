import pytest
from types import SimpleNamespace
from app.models.banking_service_deps import BankingServiceDependencies

# ---------------------------
# Fixtures for dummy dependencies
# ---------------------------

@pytest.fixture
def dummy_account_service():
    return SimpleNamespace(name="AccountServiceDummy")

@pytest.fixture
def dummy_account_repo():
    return SimpleNamespace(name="AccountRepoDummy")

@pytest.fixture
def dummy_bank_repo():
    return SimpleNamespace(name="BankRepoDummy")

@pytest.fixture
def dummy_raw_provider_repo():
    return SimpleNamespace(name="RawProviderRepoDummy")

@pytest.fixture
def dummy_banking_provider():
    return SimpleNamespace(name="PlaidSandboxDummy")


# ---------------------------
# Parametrized tests for initialization
# ---------------------------

@pytest.mark.parametrize(
    "account_service, account_repo, bank_repo, raw_provider_repo, banking_provider",
    [
        ("dummy_account_service", "dummy_account_repo", "dummy_bank_repo", "dummy_raw_provider_repo", "dummy_banking_provider"),
    ]
)
def test_banking_service_dependencies_init(
    account_service, account_repo, bank_repo, raw_provider_repo, banking_provider, request
):
    """
    Test that BankingServiceDependencies correctly initializes with all dependencies.
    """
    # Get fixture objects from fixture names
    account_service_obj = request.getfixturevalue(account_service)
    account_repo_obj = request.getfixturevalue(account_repo)
    bank_repo_obj = request.getfixturevalue(bank_repo)
    raw_provider_repo_obj = request.getfixturevalue(raw_provider_repo)
    banking_provider_obj = request.getfixturevalue(banking_provider)

    deps = BankingServiceDependencies(
        account_service=account_service_obj,
        account_repo=account_repo_obj,
        bank_repo=bank_repo_obj,
        raw_provider_repo=raw_provider_repo_obj,
        banking_provider=banking_provider_obj,
    )

    # Check that all attributes are correctly set
    assert deps.account_service == account_service_obj
    assert deps.account_repo == account_repo_obj
    assert deps.bank_repo == bank_repo_obj
    assert deps.raw_provider_repo == raw_provider_repo_obj
    assert deps.banking_provider == banking_provider_obj

# ---------------------------
# Test default dataclass representation (__repr__)
# ---------------------------

def test_banking_service_dependencies_repr(dummy_account_service, dummy_account_repo, dummy_bank_repo,
                                          dummy_raw_provider_repo, dummy_banking_provider):
    deps = BankingServiceDependencies(
        account_service=dummy_account_service,
        account_repo=dummy_account_repo,
        bank_repo=dummy_bank_repo,
        raw_provider_repo=dummy_raw_provider_repo,
        banking_provider=dummy_banking_provider,
    )
    repr_str = repr(deps)
    # __repr__ should include the class name and all attributes
    assert "BankingServiceDependencies" in repr_str
    assert "account_service" in repr_str
    assert "account_repo" in repr_str
    assert "bank_repo" in repr_str
    assert "raw_provider_repo" in repr_str
    assert "banking_provider" in repr_str
