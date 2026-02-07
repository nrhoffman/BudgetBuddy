"""
Banking service layer.

Provides high-level banking operations including institution linking,
account synchronization, transaction retrieval, and webhook handling.
Coordinates external banking providers with internal persistence layers
using structured logging and domain-specific exception handling.
"""

from datetime import datetime, timedelta
from typing import Optional, Any

from app.logger import logger
from app.tasks.plaid import sync_transactions
from app.interfaces.banking_provider import BankingProvider
from app.models.exchange_token import ExchangeToken
from app.repositories.bank_repository import BankRepository
from app.repositories.account_repository import AccountRepository
from app.services.account_service import AccountService
from app.models.transaction import Transaction
from app.exceptions import (
    ConflictError,
    DatabaseError,
    ValidationError,
    ExternalServiceError,
)


class BankingService:
    """
    Service layer for banking-related operations.

    This service manages the lifecycle of bank institutions, accounts,
    and transactions by coordinating between external banking providers
    and internal repositories and services.
    """

    def __init__(
        self,
        account_service: AccountService,
        account_repo: AccountRepository,
        bank_repo: BankRepository,
        banking_provider: Optional[BankingProvider] = None,
    ):
        self.account_service = account_service
        self.account_repo = account_repo
        self.bank_repo = bank_repo
        self.banking_provider = banking_provider

    # ---------------------------
    # Bank link token
    # ---------------------------
    def create_bank_link_token(self, user_id: str) -> dict[str, str]:
        """
        Create a bank link token for initiating account linking.

        Args:
            user_id (str): Identifier of the user requesting the link token.

        Returns:
            dict[str, str]: Provider-specific link token payload.

        Raises:
            ExternalServiceError: If the banking provider is not configured
                or token creation fails.
        """
        if not self.banking_provider:
            logger.error("Banking provider not configured")
            raise ExternalServiceError("Banking provider not configured")

        try:
            logger.info("Creating bank link token for user %s", user_id)
            return self.banking_provider.create_link_token(user_id)
        except Exception as exc:
            logger.exception("Failed to create link token for user %s", user_id)
            raise ExternalServiceError("Failed to create link token") from exc

    # ---------------------------
    # Bank account linking
    # ---------------------------
    def add_bank_institution(
        self,
        user_id: str,
        public_token: str,
        institution_id: Optional[str] = None,
        institution_name: Optional[str] = None,
    ) -> None:
        """
        Link a new bank institution and synchronize its accounts
        and transactions.

        Exchanges a public token for an access token, persists institution
        metadata, creates accounts, and applies recent transactions.

        Args:
            user_id (str): Identifier of the user linking the institution.
            public_token (str): Temporary public token from the provider.
            institution_id (Optional[str]): Provider institution identifier.
            institution_name (Optional[str]): Human-readable institution name.

        Raises:
            ConflictError: If the institution is already linked.
            ExternalServiceError: If provider interaction or syncing fails.
        """
        if not self.banking_provider:
            logger.error("Banking provider not configured")
            raise ExternalServiceError("Banking provider not configured")

        try:
            exchange_result = self.banking_provider.exchange_public_token(public_token)

            # Check if the institution is already linked
            existing_token = self.bank_repo.get_by_user(user_id, institution_id)
            if existing_token:
                raise ConflictError("Bank institution already linked")

            exchange_token = ExchangeToken(
                public_token=exchange_result.access_token,
                institution_id=institution_id,
                institution_name=institution_name,
            )

            self.bank_repo.save_token(
                user_id=user_id,
                provider="Plaid",
                item_id=exchange_result.item_id,
                exchange_token=exchange_token,
            )

            accounts = self.banking_provider.get_accounts(
                exchange_result.access_token
            ) or []
            if not accounts:
                logger.info("No accounts returned from provider for user %s", user_id)
                return

            transactions = self.get_transactions_within_dates(
                exchange_result.access_token
            )

            for account in accounts:
                self.account_service.create_account(account, user_id)
                account_txns = [
                    tx for tx in transactions if tx.account_id == account.id
                ]
                self.account_service.apply_transaction_changes(
                    user_id=user_id, added=account_txns, modified=[], removed=[]
                )

            sync_result = self.banking_provider.get_transactions_sync(
                exchange_result.access_token
            )
            self.bank_repo.save_cursor(
                user_id=user_id,
                item_id=exchange_result.item_id,
                cursor=sync_result.get("next_cursor")
            )

        except ConflictError:
            raise
        except Exception as exc:
            logger.exception("Failed to link bank accounts for user %s", user_id)
            raise ExternalServiceError("Failed to link bank accounts") from exc

    def add_bank_accounts(
            self, user_id: str,
            institution_id: Optional[str] = None
    ) -> int:
        """
        Synchronize newly added bank accounts for an existing institution.

        Args:
            user_id (str): Identifier of the user.
            institution_id (Optional[str]): Institution to sync accounts for.

        Returns:
            int: Number of newly created accounts.

        Raises:
            ValidationError: If no bank token exists for the user.
            DatabaseError: If retrieving the bank token fails.
            ExternalServiceError: If provider synchronization fails.
        """
        if not self.banking_provider:
            logger.error("Banking provider not configured")
            raise ExternalServiceError("Banking provider not configured")

        try:
            token = self.bank_repo.get_by_user(user_id, institution_id)
        except Exception as exc:
            logger.exception(
                "Database error retrieving bank token for user %s",
                user_id
            )
            raise DatabaseError("Failed to retrieve bank token") from exc

        if not token:
            raise ValidationError("No bank token found for user")
        try:
            new_accounts = self.banking_provider.get_accounts(
                token.access_token
            ) or []

            existing_accounts = self.account_repo.get_all_accounts_with_transactions(
                user_id
            )
            existing_ids = {acct.id for acct in existing_accounts}
            accounts_to_create = [
                acct for acct in new_accounts if acct.id not in existing_ids
            ]

            if not accounts_to_create:
                return 0

            transactions = self.get_transactions_within_dates(token.access_token)
            created_count = 0

            for account in accounts_to_create:
                self.account_service.create_account(account, user_id)
                account_txns = [
                    tx for tx in transactions if tx.account_id == account.id
                ]
                self.account_service.apply_transaction_changes(
                    user_id=user_id, added=account_txns, modified=[], removed=[]
                )
                created_count += 1

            return created_count
        except ValidationError:
            raise
        except Exception as exc:
            logger.exception("Failed to sync bank accounts for user %s", user_id)
            raise ExternalServiceError("Failed to sync bank accounts") from exc

    # ---------------------------
    # Plaid webhook
    # ---------------------------
    def plaid_webhook(self, payload: dict[str, Any]) -> None:
        """
        Handle incoming Plaid webhook events.

        Args:
            payload (dict[str, Any]): Raw webhook payload from the provider.
        """
        logger.info("Received Plaid webhook", extra={"payload": payload})

        webhook_type = payload.get("webhook_type")
        webhook_code = payload.get("webhook_code")
        item_id = payload.get("item_id")

        if webhook_type != "TRANSACTIONS" or webhook_code not in {
            "SYNC_UPDATES_AVAILABLE", "INITIAL_UPDATE"
        }:
            logger.info(
                "Ignoring webhook type %s / code %s",
                webhook_type,
                webhook_code
            )
            return

        self.enqueue_plaid_sync(item_id)

    def enqueue_plaid_sync(self, item_id: str) -> None:
        """
        Enqueue a background task to synchronize transactions.

        Args:
            item_id (str): Provider item identifier to sync.
        """
        logger.info("Queuing Plaid sync for item_id: %s", item_id)
        sync_transactions.delay(item_id)

    # ---------------------------
    # Utilities
    # ---------------------------
    def get_transactions_within_dates(self, access_token: str) -> list[Transaction]:
        """
        Retrieve transactions from the past 90 days.

        Args:
            access_token (str): Provider access token.

        Returns:
            list[Transaction]: List of retrieved transactions.

        Raises:
            ExternalServiceError: If the provider is not configured or
                transaction retrieval fails.
        """
        if not self.banking_provider:
            logger.error("Banking provider not configured")
            raise ExternalServiceError("Banking provider not configured")
        try:
            end_date = datetime.today().date()
            start_date = end_date - timedelta(days=90)

            transactions = self.banking_provider.get_transactions(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date
            )
            return transactions or []
        except Exception as exc:
            logger.exception("Failed to fetch transactions for access_token")
            raise ExternalServiceError("Failed to fetch transactions") from exc
