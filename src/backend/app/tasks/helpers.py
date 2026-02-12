"""
Factory for creating a Plaid task execution context.

This module provides a helper function to build a fully initialized
PlaidTaskContext, containing all repositories, services, and the
PlaidSandbox provider required for synchronizing transactions in
background tasks or Celery workers.
"""

from sqlalchemy.orm import Session

from app.models.plaid_task_context import PlaidTaskContext
from app.providers.plaid_sandbox import PlaidSandbox
from app.repositories.account_repository import AccountRepository
from app.repositories.bank_repository import BankRepository
from app.repositories.raw_provider_repository import RawProviderRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.account_service import AccountService


def build_plaid_sync_context(db: Session) -> PlaidTaskContext:
    """
    Construct a fully initialized PlaidTaskContext for transaction sync tasks.

    This function instantiates all required repositories, the AccountService,
    and the PlaidSandbox provider, bundling them into a PlaidTaskContext
    object that can be passed to Celery tasks or other background jobs.

    Args:
        db (Session): Active SQLAlchemy session for database access.

    Returns:
        PlaidTaskContext: Context object containing repositories, services,
                          and the Plaid provider.
    """

    bank_repo = BankRepository(db)
    account_repo = AccountRepository(db)
    txn_repo = TransactionRepository(db)
    raw_provider_repo = RawProviderRepository(db)

    account_service = AccountService(
        account_repo=account_repo,
        bank_repo=bank_repo,
        txn_repo=txn_repo,
    )

    return PlaidTaskContext(
        db=db,
        bank_repo=bank_repo,
        account_repo=account_repo,
        txn_repo=txn_repo,
        raw_provider_repo=raw_provider_repo,
        account_service=account_service,
        plaid=PlaidSandbox(),
    )
