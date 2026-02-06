"""
Abstract interface for banking providers.

Defines the methods required for linking accounts, exchanging tokens,
and retrieving account and transaction data.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.account import Account
from app.models.transaction import Transaction


class BankingProvider(ABC):
    """Abstract base class for a banking provider integration."""

    name: str

    @abstractmethod
    def create_link_token(self, user_id: str) -> str:
        """
        Create a Plaid link token for a user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            str: A Plaid link token that can be used in the client app.

        Raises:
            ApiException: If the Plaid API call fails.
            Exception: For any unexpected errors.
        """

    @abstractmethod
    def exchange_public_token(self, public_token: str) -> str:
        """
        Exchange a public token for an access token.

        Args:
            public_token (str): Public token returned by Plaid Link.

        Returns:
            str: Access token for the user account.

        Raises:
            ApiException: If the Plaid API call fails.
            Exception: For any unexpected errors.
        """

    @abstractmethod
    def get_accounts(self, access_token: str) -> list[Account]:
        """
        Fetch accounts associated with a given access token.

        Args:
            access_token (str): Plaid access token for the user.

        Returns:
            list[Account]: List of Account domain models.

        Raises:
            ApiException: If the Plaid API call fails.
            Exception: For any unexpected errors.
        """

    @abstractmethod
    def get_transactions(
        self, access_token: str, start_date: str, end_date: str
    ) -> list[Transaction]:
        """
        Fetch transactions for an account within a specified date range.

        Args:
            access_token (str): Plaid access token for the user.
            start_date (str): Start date (YYYY-MM-DD) for transactions.
            end_date (str): End date (YYYY-MM-DD) for transactions.

        Returns:
            list[Transaction]: List of mapped Transaction domain models.

        Raises:
            ApiException: If the Plaid API call fails.
            Exception: For any unexpected errors.
        """

    @abstractmethod
    def get_transactions_sync(
        self,
        access_token: str,
        cursor: Optional[str] = None
    ) -> dict:
        """
        Incrementally fetch transactions using Plaid's transactions_sync endpoint.

        Args:
            access_token (str): Plaid access token.
            cursor (Optional[str]): Optional cursor for incremental updates.

        Returns:
            dict: Dictionary with sorted added, modified, removed transactions
                  and the next_cursor.

        Raises:
            ApiException: If the Plaid API call fails.
            Exception: For any unexpected errors.
        """

    @abstractmethod
    def sort_transactions(self, txns: list[Transaction]) -> list[Transaction]:
        """
        Sort transactions deterministically by date and transaction ID.

        Args:
            txns (list[Transaction]): List of Transaction objects.

        Returns:
            list[Transaction]: Sorted list of transactions.

        Raises:
            Exception: If sorting fails.
        """

    @abstractmethod
    def map_plaid_transaction(self, txn) -> Transaction:
        """
        Map a Plaid transaction object to the Transaction domain model.

        Args:
            txn: Plaid transaction object.

        Returns:
            Transaction: Mapped Transaction domain model.

        Raises:
            Exception: If mapping fails.
        """
