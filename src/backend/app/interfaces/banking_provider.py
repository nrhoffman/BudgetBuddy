"""
Abstract interface for banking providers.

Defines the methods required for linking accounts, exchanging tokens,
and retrieving account and transaction data.
"""

from abc import ABC, abstractmethod
from typing import List

from app.models.account import Account
from app.models.transaction import Transaction


class BankingProvider(ABC):
    """Abstract base class for a banking provider integration."""

    name: str

    @abstractmethod
    def create_link_token(self, user_id: str) -> str:
        """
        Generate a link token for a user to connect their bank account.

        Args:
            user_id: Internal user identifier.

        Returns:
            Provider-generated link token.
        """

    @abstractmethod
    def exchange_public_token(self, public_token: str) -> str:
        """
        Exchange a public token for a provider-specific access token.

        Args:
            public_token: Temporary public token from the provider.

        Returns:
            Long-lived access token.
        """

    @abstractmethod
    def get_accounts(self, access_token: str) -> List[Account]:
        """
        Retrieve accounts associated with an access token.

        Args:
            access_token: Provider access token.

        Returns:
            List of linked accounts.
        """

    @abstractmethod
    def get_transactions(
        self,
        access_token: str,
        start_date: str,
        end_date: str,
    ) -> List[Transaction]:
        """
        Retrieve transactions between two dates.

        Args:
            access_token: Provider access token.
            start_date: ISO start date.
            end_date: ISO end date.

        Returns:
            List of transactions.
        """

    @abstractmethod
    def get_transactions_sync(
        self,
        access_token: str,
        cursor: str | None
    ) -> str:
        """
        Retrieve transactions between two dates.

        Args:
            access_token: Provider access token.
            start_date: ISO start date.
            end_date: ISO end date.

        Returns:
            List of transactions.
        """
