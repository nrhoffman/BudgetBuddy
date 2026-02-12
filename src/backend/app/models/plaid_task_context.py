"""
Plaid task execution context.

This module defines a dataclass that encapsulates all dependencies
required to execute background tasks interacting with Plaid.
It simplifies task functions by grouping the database session,
repositories, services, and external provider into a single container.
"""

from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.repositories.account_repository import AccountRepository
from app.repositories.bank_repository import BankRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.raw_provider_repository import RawProviderRepository
from app.services.account_service import AccountService
from app.providers.plaid_sandbox import PlaidSandbox


@dataclass
class PlaidTaskContext:
    """
    Context container for Plaid background tasks.

    Attributes:
        db (Session): Active SQLAlchemy database session.
        bank_repo (BankRepository): Repository for managing
        bank tokens and institutions.
        account_repo (AccountRepository): Repository for account
        persistence operations.
        txn_repo (TransactionRepository): Repository for transaction
        persistence operations.
        raw_provider_repo (RawProviderRepository): Repository for
        storing raw provider events.
        account_service (AccountService): Service for managing
        accounts and applying transactions.
        plaid (PlaidSandbox): Plaid sandbox provider integration
        instance.

    This dataclass exists to simplify dependency injection in Celery
    tasks or other background jobs interacting with Plaid, allowing
    all required resources to be accessed via a single object.
    """

    db: Session
    bank_repo: BankRepository
    account_repo: AccountRepository
    txn_repo: TransactionRepository
    raw_provider_repo: RawProviderRepository
    account_service: AccountService
    plaid: PlaidSandbox
