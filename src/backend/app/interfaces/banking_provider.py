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
    def get_transactions_sync(
        self,
        access_token: str,
        accounts: list[Account],
        cursor: Optional[str] = None
    ) -> dict:
        """
        Incrementally fetch transactions using Plaid's transactions_sync endpoint.

        Args:
            access_token (str): Plaid access token.
            accounts (list[Account]): Accounts for access_token
            cursor (Optional[str]): Optional cursor for incremental updates.

        Returns:
            dict: Dictionary with sorted added, modified, removed transactions
                  and the next_cursor.

        Raises:
            ApiException: If the Plaid API call fails.
            Exception: For any unexpected errors.
        """

    @abstractmethod
    def get_institution_by_id(self, institution_id: str) -> dict:
        """
        Retrieve institution metadata from Plaid by institution ID.

        This method calls Plaid's `/institutions/get_by_id` endpoint to fetch
        metadata for a specific financial institution, including optional
        fields such as the institution logo, primary brand color, and website URL.

        The returned logo (if present) is Base64-encoded and must be decoded
        before being stored or served by the application.

        Args:
            institution_id (str): The Plaid institution ID (e.g., "ins_3").

        Returns:
            dict: A dictionary representation of the institution object.
                Returns an empty dictionary if no institution_id is provided.

        Notes:
            - This method does not require an access token.
            - The response includes optional metadata only if
            `include_optional_metadata=True`.
            - Institution logos are returned as Base64-encoded PNG images.
        """
