"""
Banking service layer.

This module defines business logic for integrating with external banking
providers. It handles link token creation, account linking, and
synchronization of bank accounts and transactions through the account
service. Includes structured logging and HTTPException handling.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status

from app.logger import logger
from app.tasks.plaid import sync_transactions
from app.interfaces.banking_provider import BankingProvider
from app.models.exchange_token import ExchangeToken
from app.repositories.bank_repository import BankRepository
from app.repositories.account_repository import AccountRepository
from app.services.account_service import AccountService
from app.models.transaction import Transaction


class BankingService:
    """
    Service layer for banking-related operations.

    Handles interaction with external banking providers and coordinates
    account and transaction persistence via AccountService.
    """

    def __init__(
        self,
        account_service: AccountService,
        account_repo: AccountRepository,
        bank_repo: BankRepository,
        banking_provider: Optional[BankingProvider] = None,
    ):
        """
        Initialize the BankingService.

        Args:
            account_service: Service for account and transaction persistence.
            account_repo: Repository for account data.
            bank_repo: Repository for bank tokens and cursors.
            banking_provider: Optional external banking provider implementation.
        """
        self.account_service = account_service
        self.account_repo = account_repo
        self.bank_repo = bank_repo
        self.banking_provider = banking_provider

    # ---------------------------
    # Bank link token
    # ---------------------------
    def create_bank_link_token(self, user_id: str) -> Dict[str, str]:
        """
        Create a bank link token for a user.

        Args:
            user_id: Identifier of the authenticated user.

        Returns:
            Dictionary containing the provider-generated link token.

        Raises:
            HTTPException: If banking provider is not configured.
        """
        if not self.banking_provider:
            logger.error("Banking provider not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Banking provider not configured",
            )

        try:
            logger.info("Creating bank link token for user %s", user_id)
            return self.banking_provider.create_link_token(user_id)
        except Exception as exc:
            logger.exception("Failed to create link token for user %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create link token",
            ) from exc

    # ---------------------------
    # Bank account linking
    # ---------------------------
    def add_bank_accounts(
        self,
        user_id: str,
        public_token: str,
        institution_id: Optional[str] = None,
        institution_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Exchange a public token and sync bank accounts and transactions.

        Args:
            user_id: Identifier of the authenticated user.
            public_token: Public token returned by the banking provider.
            institution_id: Optional institution ID.
            institution_name: Optional institution name.

        Returns:
            Dictionary with status and number of accounts added.

        Raises:
            HTTPException: If provider is not configured or sync fails.
        """
        if not self.banking_provider:
            logger.error("Banking provider not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Banking provider not configured",
            )

        try:
            exchange_result = self.banking_provider.exchange_public_token(public_token)

            existing_token = self.bank_repo.get_by_user(user_id, institution_id)
            if existing_token:
                return {
                    "status": "already_linked",
                    "institution_id": institution_id,
                    "institution_name": institution_name,
                    "item_id": existing_token.item_id,
                }

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
                return {"status": "linked", "accounts_added": 0}

            all_transactions = self.get_transactions_within_dates(
                access_token=exchange_result.access_token,

            )

            for account in accounts:
                self.account_service.create_account(account, user_id)
                account_transactions = [
                    tx for tx in all_transactions if tx.account_id == account.id
                ]
                self.account_service.apply_transaction_changes(
                    user_id=user_id, added=account_transactions, modified=[], removed=[]
                )

            sync_result = self.banking_provider.get_transactions_sync(
                exchange_result.access_token
            )
            self.bank_repo.save_cursor(user_id=user_id,
                                       item_id=exchange_result.item_id,
                                       cursor=sync_result["next_cursor"]
            )

            return {"status": "linked", "accounts_added": len(accounts)}

        except Exception as exc:
            logger.exception("Failed to link bank accounts for user %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to link bank accounts",
            ) from exc

    # ---------------------------
    # Plaid webhook
    # ---------------------------
    def plaid_webhook(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Handle Plaid webhook events.

        Args:
            payload: Webhook payload from Plaid.

        Returns:
            Dictionary indicating processing status.
        """
        logger.info("Received Plaid webhook", extra={"payload": payload})

        webhook_type = payload.get("webhook_type")
        webhook_code = payload.get("webhook_code")
        item_id = payload.get("item_id")

        if webhook_type != "TRANSACTIONS" or webhook_code not in {
            "SYNC_UPDATES_AVAILABLE", "INITIAL_UPDATE"
        }:
            return {"status": "ignored"}

        self.enqueue_plaid_sync(item_id)
        return {"status": "ok"}

    def enqueue_plaid_sync(self, item_id: str) -> None:
        """
        Queue a background task to sync transactions for the given item.

        Args:
            item_id: Identifier of the bank item to sync.
        """
        logger.info("Queuing Plaid sync for item_id: %s", item_id)
        sync_transactions.delay(item_id)

    # ---------------------------
    # Utilities
    # ---------------------------
    def get_transactions_within_dates(self, access_token: str) -> List[Transaction]:
        """
        Fetch transactions for the past 90 days for a given access token.

        Args:
            access_token (str): The Plaid (or other banking provider) access token
                                for the user's account.

        Returns:
            List[Transaction]: A list of Transaction objects within the date range.

        Raises:
            RuntimeError: If the banking provider fails to fetch transactions.
        """
        try:
            end_date = datetime.today().date()
            start_date = end_date - timedelta(days=90)

            all_transactions = self.banking_provider.get_transactions(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date
            )

            return all_transactions

        except Exception as exc:
            logger.exception(
                "Failed to fetch transactions for access_token %s: %s",
                access_token,
                exc
            )
            raise RuntimeError(
                f"Error fetching transactions for access_token {access_token}"
            ) from exc
