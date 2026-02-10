import pytest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session
from app.tasks.helpers import build_plaid_sync_context
from app.models.plaid_task_context import PlaidTaskContext
from app.repositories.account_repository import AccountRepository
from app.repositories.bank_repository import BankRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.raw_provider_repository import RawProviderRepository
from app.services.account_service import AccountService
from app.providers.plaid_sandbox import PlaidSandbox

# ---------------------------
# Fixtures
# ---------------------------

@pytest.fixture
def mock_db():
    """Return a mock SQLAlchemy session."""
    return MagicMock(spec=Session)

# ---------------------------
# Test build_plaid_sync_context
# ---------------------------

@pytest.mark.parametrize("db_session", [None, "mock_db"])
def test_build_plaid_sync_context(db_session, mock_db):
    """Ensure the context is correctly built and all attributes exist."""
    session = mock_db if db_session == "mock_db" else MagicMock(spec=Session)
    context = build_plaid_sync_context(session)
    
    # Check return type
    assert isinstance(context, PlaidTaskContext)
    
    # Check all attributes exist
    assert context.db == session
    assert isinstance(context.bank_repo, BankRepository)
    assert isinstance(context.account_repo, AccountRepository)
    assert isinstance(context.txn_repo, TransactionRepository)
    assert isinstance(context.raw_provider_repo, RawProviderRepository)
    assert isinstance(context.account_service, AccountService)
    assert isinstance(context.plaid, PlaidSandbox)
    
    # AccountService should reference the correct repos
    assert context.account_service.account_repo == context.account_repo
    assert context.account_service.bank_repo == context.bank_repo
    assert context.account_service.txn_repo == context.txn_repo
