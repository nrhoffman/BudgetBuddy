"""
Plaid sandbox integration implementing the BankingProvider interface.

This module provides a PlaidSandbox class which implements the BankingProvider
interface using Plaid's sandbox environment. It supports creating link tokens,
exchanging public tokens, fetching account balances, retrieving transactions,
and performing incremental transaction syncs.
"""

import os
from typing import Optional

from plaid import ApiClient, Configuration
from plaid.api import plaid_api
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest

from app.models.account import Account, parse_account_type, parse_account_subtype
from app.models.transaction import Transaction
from app.interfaces.banking_provider import BankingProvider


class PlaidSandbox(BankingProvider):
    """
    Plaid sandbox implementation for testing account and transaction APIs.

    Provides methods to create link tokens, exchange public tokens for access
    tokens, fetch accounts and transactions, and perform incremental transaction
    synchronization using Plaid's sandbox environment.

    Attributes:
        name (str): The name of the banking provider ("plaid").
        client (plaid_api.PlaidApi): Configured Plaid API client instance.
    """
    name: str = "plaid"

    def __init__(self):
        """Initialize the Plaid API client using sandbox credentials."""
        configuration = Configuration(
            host="https://sandbox.plaid.com",
            api_key={
                "clientId": os.getenv("PLAID_CLIENT_ID"),
                "secret": os.getenv("PLAID_SECRET"),
            },
        )
        self.client = plaid_api.PlaidApi(ApiClient(configuration))

    def create_link_token(self, user_id: str) -> str:
        """
        Create a Plaid link token for a user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            str: A Plaid link token that can be used in the client app.
        """
        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=user_id),
            client_name="Budget Buddy",
            products=[
                Products("transactions"),
                Products("auth"),
                Products("liabilities"),
                Products("investments"),
            ],
            country_codes=[CountryCode("US")],
            language="en",
        )
        response = self.client.link_token_create(request)
        return response.link_token

    def exchange_public_token(self, public_token: str) -> str:
        """
        Exchange a public token for an access token.

        Args:
            public_token (str): Public token returned by Plaid Link.

        Returns:
            str: Access token for the user account.
        """
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self.client.item_public_token_exchange(request)
        return response

    def get_accounts(self, access_token: str) -> list[Account]:
        """
        Fetch accounts associated with a given access token.

        Args:
            access_token (str): Plaid access token for the user.

        Returns:
            list[Account]: List of Account domain models.
        """
        request = AccountsBalanceGetRequest(access_token=access_token)
        res = self.client.accounts_balance_get(request)
        accounts = []
        for acc in res.accounts:
            accounts.append(
                Account(
                    id=acc.account_id,
                    name=acc.name,
                    type=parse_account_type(acc.type),
                    subtype=parse_account_subtype(acc.subtype),
                    balance=acc.balances.current,
                )
            )
        return accounts

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
        """
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
        )
        res = self.client.transactions_get(request)
        transactions = [self.map_plaid_transaction(txn) for txn in res.transactions]
        return self.sort_transactions(transactions)

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
        """
        has_more = True
        added: list[Transaction] = []
        modified: list[Transaction] = []
        removed: list[str] = []

        while has_more:
            request = TransactionsSyncRequest(
                access_token=access_token, cursor=cursor
            ) if cursor else TransactionsSyncRequest(access_token=access_token)

            res = self.client.transactions_sync(request)

            added.extend(map(self.map_plaid_transaction, res.added))
            modified.extend(map(self.map_plaid_transaction, res.modified))
            removed.extend(
                txn["transaction_id"] if isinstance(txn, dict) else txn
                for txn in res.removed
            )

            cursor = res.next_cursor
            has_more = res.has_more

        return {
            "added": self.sort_transactions(added),
            "modified": self.sort_transactions(modified),
            "removed": removed,
            "next_cursor": cursor,
        }

    def sort_transactions(self, txns: list[Transaction]) -> list[Transaction]:
        """
        Sort transactions deterministically by date and transaction ID.

        Args:
            txns (list[Transaction]): List of Transaction objects.

        Returns:
            list[Transaction]: Sorted list of transactions.
        """
        return sorted(txns, key=lambda t: (t.date, t.transaction_id))

    def map_plaid_transaction(self, txn) -> Transaction:
        """
        Map a Plaid transaction object to the Transaction domain model.

        Args:
            txn: Plaid transaction object.

        Returns:
            Transaction: Mapped Transaction domain model.
        """
        pfc = getattr(txn, "personal_finance_category", None)
        return Transaction(
            transaction_id=txn.transaction_id,
            account_id=txn.account_id,
            name=txn.name,
            merchant_name=getattr(txn, "merchant_name", None),
            amount=txn.amount,
            date=txn.date,
            category_primary=getattr(pfc, "primary", None) if pfc else None,
            category_detailed=getattr(pfc, "detailed", None) if pfc else None,
            category_confidence_level=getattr(
                pfc,
                "confidence_level",
                None
            ) if pfc else None,
            pending=getattr(txn, "pending", None),
            iso_currency_code=getattr(txn, "iso_currency_code", None),
            unofficial_currency_code=getattr(txn, "unofficial_currency_code", None),
        )
