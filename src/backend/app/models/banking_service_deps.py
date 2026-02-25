"""
Banking service dependency container.

This module defines a dataclass that aggregates all dependencies
required by the `BankingService`. It is intended to simplify
initialization and dependency injection by grouping services,
repositories, and external providers into a single container.
"""

from dataclasses import dataclass

from app.providers.plaid_sandbox import PlaidSandbox
from app.repositories.bank_repository import BankRepository
from app.repositories.raw_provider_repository import RawProviderRepository
from app.services.account_service import AccountService


@dataclass
class BankingServiceDependencies:
    """
    Container for all dependencies of the BankingService.

    Attributes:
        account_service (AccountService): Service for managing accounts
        and transactions.
        bank_repo (BankRepository): Repository for managing bank tokens and
        institution data.
        raw_provider_repo (RawProviderRepository): Repository for storing raw
        provider events.
        banking_provider (PlaidSandbox): External banking provider integration
        instance.

    This dataclass exists to simplify initialization of the
    `BankingService`, allowing all required dependencies to be
    passed around as a single object.
    """
    account_service: AccountService
    bank_repo: BankRepository
    raw_provider_repo: RawProviderRepository
    banking_provider: PlaidSandbox
