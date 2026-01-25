"""
Banking service layer.

This module defines business logic for integrating with external banking
providers. It handles link token creation, account linking, and
synchronization of bank accounts and transactions through the account
service.
"""

from datetime import datetime, timedelta

from fastapi import HTTPException, status

from app.logger import logger
from app.interfaces.banking_provider import BankingProvider
from app.services.account_service import AccountService


class BankingService:
    """
    Service layer for banking-related operations.

    Handles interaction with external banking providers and coordinates
    account and transaction persistence via AccountService.
    """

    def __init__(
        self,
        account_service: AccountService,
        banking_provider: BankingProvider | None = None,
    ):
        """
        Initialize the BankingService.

        Args:
            account_service: Service for account and transaction persistence.
            banking_provider: External banking provider implementation.
        """
        self.account_service = account_service
        self.banking_provider = banking_provider

    def create_bank_link_token(self, user_id: str) -> dict:
        """
        Create a bank link token for a user.

        Args:
            user_id: Identifier of the authenticated user.

        Returns:
            dict: Provider-generated link token payload.

        Raises:
            HTTPException: If the banking provider is not configured.
        """
        if not self.banking_provider:
            logger.error("Banking provider not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Banking provider not configured",
            )

        logger.info("Creating bank link token for user %s", user_id)
        return self.banking_provider.create_link_token(user_id)

    def add_bank_accounts(self, user_id: str, public_token: str) -> dict:
        """
        Exchange a public token and sync bank accounts and transactions.

        Args:
            user_id: Identifier of the authenticated user.
            public_token: Public token returned by the banking provider.

        Returns:
            dict: Status message and number of accounts added.

        Raises:
            HTTPException: If provider is not configured or sync fails.
        """
        if not self.banking_provider:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Banking provider not configured",
            )

        try:
            access_token = self.banking_provider.exchange_public_token(
                public_token
            )

            accounts = self.banking_provider.get_accounts(access_token)

            end_date = datetime.today().date()
            start_date = end_date - timedelta(days=90)

            for account in accounts:
                self.account_service.create_account(account, user_id)

                transactions = self.banking_provider.get_transactions(
                    access_token,
                    start_date,
                    end_date,
                )

                for txn in transactions:
                    self.account_service.add_transaction(
                        user_id,
                        account.id,
                        txn,
                    )

            return {
                "status": "linked",
                "accounts_added": len(accounts),
            }

        except Exception as exc:
            logger.error(
                "Failed to link bank accounts for user %s: %s",
                user_id,
                exc,
                exc_info=True,
            )
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to link bank accounts",
            ) from exc
