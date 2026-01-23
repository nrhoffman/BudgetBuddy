"""
Abstract interface for banking providers.

Defines the methods required for linking accounts, exchanging tokens, and
retrieving account and transaction data.
"""

from typing import List
from app.models.account import Account
from app.models.transaction import Transaction


class BankingProvider:
    """Abstract base class for a banking provider integration."""

    name: str

    def create_link_token(self, user_id: str) -> str:
        """Generate a link token for a user to connect their bank account."""
        ...

    def exchange_public_token(self, public_token: str) -> str:
        """Exchange a public token for a provider-specific access token."""
        ...

    def get_accounts(self, access_token: str) -> List[Account]:
        """Retrieve accounts for the given access token."""
        ...

    def get_transactions(
        self,
        access_token: str,
        start_date: str,
        end_date: str
    ) -> List[Transaction]:
        """Retrieve transactions for an account between two dates."""
        ...
