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
from app.mappers.transaction_mapper import map_plaid_transaction, sort_transactions
from app.models.exchange_token import ExchangeToken
from app.models.account import Account, parse_account_type, parse_account_subtype
from app.models.transaction import Transaction
from app.models.raw_provider_data import RawProviderData, Identity
from app.models.banking_service_deps import BankingServiceDependencies
from app.exceptions import (
    ConflictError,
    DatabaseError,
    ValidationError,
    ExternalServiceError,
)
from app.mappers.account_index import AccountIndex


class BankingService:
    """
    Service layer for banking-related operations.

    This service manages the lifecycle of bank institutions, accounts,
    and transactions by coordinating between external banking providers
    and internal repositories and services.
    """

    def __init__(self, deps: BankingServiceDependencies):
        self.banking_deps = deps

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
        if not self.banking_deps.banking_provider:
            logger.error("Banking provider not configured")
            raise ExternalServiceError("Banking provider not configured")

        try:
            logger.info("Creating bank link token for user %s", user_id)
            return self.banking_deps.banking_provider.create_link_token(user_id)
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
        if not self.banking_deps.banking_provider:
            logger.error("Banking provider not configured")
            raise ExternalServiceError("Banking provider not configured")

        try:
            exchange_result = (
                self.banking_deps.banking_provider.exchange_public_token(
                    public_token
                )
            )

            # Check if the institution is already linked
            if self.banking_deps.bank_repo.get_by_user(user_id, institution_id):
                raise ConflictError("Bank institution already linked")

            self.banking_deps.bank_repo.save_token(
                user_id=user_id,
                provider="plaid",
                item_id=exchange_result.item_id,
                exchange_token=ExchangeToken(
                    public_token=exchange_result.access_token,
                    institution_id=institution_id,
                    institution_name=institution_name,
                ),
            )

            acc_res = self.banking_deps.banking_provider.get_accounts(
                exchange_result.access_token
            )
            if not acc_res:
                logger.info(
                    "No accounts returned from provider for user %s",
                    user_id
                )
                return

            self.banking_deps.raw_provider_repo.save(
                RawProviderData(
                    provider="plaid",
                    endpoint="accounts_balance_get",
                    payload=acc_res.to_dict(),
                    identity=Identity(
                        user_id=user_id,
                        item_id=exchange_result.item_id
                    )
                )
            )

            accounts = [
                Account(
                    id=acc.account_id,
                    name=acc.name,
                    type=parse_account_type(acc.type),
                    subtype=parse_account_subtype(acc.subtype),
                    balance=acc.balances.current,
                )
                for acc in acc_res.accounts
            ]

            account_index = AccountIndex(accounts)

            # Get's first 30 days
            txn_res = self.get_transactions_within_dates(
                exchange_result.access_token
            )

            self.banking_deps.raw_provider_repo.save(
                RawProviderData(
                    provider="plaid",
                    endpoint="transactions_get",
                    payload=txn_res.to_dict(),
                    identity=Identity(
                        user_id=user_id,
                        item_id=exchange_result.item_id
                    )
                )
            )

            transactions = sort_transactions([
                map_plaid_transaction(
                    txn,
                    account_type=account_index.type_for(txn.account_id)
                ) for txn in txn_res.transactions
            ])

            for account in accounts:
                self.banking_deps.account_service.create_account(account, user_id)
                account_txns = [
                    tx for tx in transactions if tx.account_id == account.id
                ]
                self.banking_deps.account_service.apply_transaction_changes(
                    user_id=user_id, added=account_txns, modified=[], removed=[]
                )

            # Gets initial cursor and saves it
            sync_result = self.banking_deps.banking_provider.get_transactions_sync(
                exchange_result.access_token,
                accounts
            )
            self.banking_deps.bank_repo.save_cursor(
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
        if not self.banking_deps.banking_provider:
            logger.error("Banking provider not configured")
            raise ExternalServiceError("Banking provider not configured")

        try:
            token = self.banking_deps.bank_repo.get_by_user(user_id, institution_id)
        except Exception as exc:
            logger.exception(
                "Database error retrieving bank token for user %s",
                user_id
            )
            raise DatabaseError("Failed to retrieve bank token") from exc

        if not token:
            raise ValidationError("No bank token found for user")
        try:
            new_acc_res = self.banking_deps.banking_provider.get_accounts(
                token.access_token
            )

            self.banking_deps.raw_provider_repo.save(
                RawProviderData(
                    provider="plaid",
                    endpoint="accounts_balance_get",
                    payload=new_acc_res.to_dict(),
                    identity=Identity(user_id=user_id, item_id=token.item_id)
                )
            )

            existing_ids = {acct.id for acct in (
                self.banking_deps.account_repo.get_all_accounts_with_transactions(
                    user_id
                )
            )}

            accounts_to_create = [
                Account(
                    id=acc.account_id,
                    name=acc.name,
                    type=parse_account_type(acc.type),
                    subtype=parse_account_subtype(acc.subtype),
                    balance=acc.balances.current,
                )
                for acc in new_acc_res.accounts
                if acc.account_id not in existing_ids
            ]

            if not accounts_to_create:
                return 0

            account_index = AccountIndex(accounts_to_create)

            new_txns_res = self.get_transactions_within_dates(token.access_token)
            transactions = sort_transactions([
                map_plaid_transaction(
                    txn,
                    account_index.type_for(txn.account_id)
                ) for txn in new_txns_res.transactions
            ])

            self.banking_deps.raw_provider_repo.save(
                RawProviderData(
                    provider="plaid",
                    endpoint="transactions_get",
                    payload=new_txns_res.to_dict(),
                    identity=Identity(user_id=user_id, item_id=token.item_id)
                )
            )

            created_count = 0

            for account in accounts_to_create:
                self.banking_deps.account_service.create_account(account, user_id)
                account_txns = [
                    tx for tx in transactions if tx.account_id == account.id
                ]
                self.banking_deps.account_service.apply_transaction_changes(
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

        webhook_res_model = RawProviderData(
            provider="plaid",
            endpoint="webhook",
            payload=payload,
        )

        self.banking_deps.raw_provider_repo.save(webhook_res_model)

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
        if not self.banking_deps.banking_provider:
            logger.error("Banking provider not configured")
            raise ExternalServiceError("Banking provider not configured")
        try:
            end_date = datetime.today().date()
            start_date = end_date - timedelta(days=90)

            transactions = self.banking_deps.banking_provider.get_transactions(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date
            )
            return transactions
        except Exception as exc:
            logger.exception("Failed to fetch transactions for access_token")
            raise ExternalServiceError("Failed to fetch transactions") from exc
