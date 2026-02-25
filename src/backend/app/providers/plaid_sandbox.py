"""
Plaid sandbox integration implementing the BankingProvider interface.

This module provides a PlaidSandbox class which implements the BankingProvider
interface using Plaid's sandbox environment. It supports creating link tokens,
exchanging public tokens, fetching account balances, retrieving transactions,
and performing incremental transaction syncs.
"""

import os
from typing import Optional, Any

from plaid import ApiClient, Configuration
from plaid.api import plaid_api
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.link_token_create_request_update import LinkTokenCreateRequestUpdate
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest

from app.mappers.transaction_mapper import map_plaid_transaction, sort_transactions
from app.mappers.account_mapper import map_plaid_account
from app.mappers.account_index import AccountIndex
from app.models.transaction import Transaction
from app.models.account import Account
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
    
    def create_update_link_token(self, user_id: str, access_token: str) -> str:
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
            access_token=access_token,
            update=LinkTokenCreateRequestUpdate(
                account_selection_enabled=True
            )
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

    def get_accounts(self, access_token: str,
                     institution_id: str,
                     institution_logo: str | None = None
                     ) -> dict[str, Any]:

        request = AccountsBalanceGetRequest(access_token=access_token)
        res = self.client.accounts_balance_get(request)

        accounts = [
            map_plaid_account(
                acc,
                institution_id=institution_id,
                institution_logo=institution_logo
            )
            for acc in res.accounts
        ]

        return {
            "accounts": accounts,
            "raw_pages": res.to_dict()
        }

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
            accounts (list[Account]): List of accounts for access_token
            cursor (Optional[str]): Optional cursor for incremental updates.

        Returns:
            dict: Dictionary with sorted added, modified, removed transactions
                  the next_cursor, and raw data.
        """
        has_more = True
        added: list[Transaction] = []
        modified: list[Transaction] = []
        removed: list[str] = []
        raw_pages: list[dict] = []

        account_index = AccountIndex(accounts)

        while has_more:
            request = TransactionsSyncRequest(
                access_token=access_token, cursor=cursor
            ) if cursor else TransactionsSyncRequest(access_token=access_token)

            res = self.client.transactions_sync(request)

            raw_pages.append(res.to_dict())

            added.extend([
                map_plaid_transaction(
                    tx, account_index.type_for(tx.account_id)
                ) for tx in res.added
            ])
            modified.extend([
                map_plaid_transaction(
                    tx, account_index.type_for(tx.account_id)
                ) for tx in res.modified
            ])
            removed.extend(
                txn["transaction_id"] if isinstance(txn, dict) else txn
                for txn in res.removed
            )

            cursor = res.next_cursor
            has_more = res.has_more

        return {
            "added": sort_transactions(added),
            "modified": sort_transactions(modified),
            "removed": removed,
            "next_cursor": cursor,
            "raw": raw_pages
        }

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
        if not institution_id:
            return {}

        inst_request = InstitutionsGetByIdRequest(
            institution_id=institution_id,
            country_codes=[CountryCode("US")],
            options={"include_optional_metadata": True},
        )

        inst_response = self.client.institutions_get_by_id(inst_request)

        return inst_response.institution.to_dict()
