"""
Account indexing utilities.

This module provides lightweight helpers for efficiently accessing
account metadata by account ID during transaction ingestion and mapping.

Provider transaction payloads often lack sufficient account-level context
(e.g. account type or subtype). Rather than performing repeated linear
searches over account collections, this module enables O(1) lookups
by pre-indexing accounts once per ingestion or sync operation.
"""

from app.models.account import Account, AccountType


class AccountIndex:
    """
    Index for fast account metadata lookup by account ID.

    This class precomputes a mapping of account IDs to Account objects,
    allowing transaction-mapping logic to enrich transactions with
    account-level attributes that are not included in provider payloads.

    The index is intended to be short-lived and request-scoped, created
    during account synchronization or transaction ingestion and discarded
    afterward.

    Attributes:
        _by_id (dict[str, Account]): Internal mapping of account ID to
            Account instance.
    """

    def __init__(self, accounts: list[Account]) -> None:
        """
        Create an AccountIndex from a list of accounts.

        Args:
            accounts (list[Account]): The accounts to index. Each account's
                `id` must be unique within the list.

        Raises:
            ValueError: If duplicate account IDs are present.
        """
        seen_ids = set()
        for acc in accounts:
            if acc.id in seen_ids:
                raise ValueError(f"Duplicate account ID detected: {acc.id}")
            seen_ids.add(acc.id)
        self._by_id = {acc.id: acc for acc in accounts}

    def type_for(self, account_id: str) -> AccountType:
        """
        Retrieve the account type for a given account ID.

        Args:
            account_id (str): The provider-specific account identifier.

        Returns:
            AccountType: The type of the account associated with the ID,
            or None if the account ID is not present in the index.
        """
        acct = self._by_id.get(account_id)
        if acct is None:
            return None
        return acct.type
