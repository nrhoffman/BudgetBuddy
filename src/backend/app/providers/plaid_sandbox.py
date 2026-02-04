"""
Plaid sandbox integration implementing the BankingProvider interface.

This module provides a PlaidSandbox class which implements the BankingProvider
interface using Plaid's sandbox environment. It supports creating link tokens,
exchanging public tokens, fetching account balances, retrieving transactions,
and performing incremental transaction syncs. All methods include logging and
error handling for both API-specific and unexpected exceptions.
"""

import os
from typing import List, Optional

from plaid import ApiClient, ApiException, Configuration
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
from app.logger import logger


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

        Raises:
            ApiException: If the Plaid API call fails.
            Exception: For any unexpected errors.
        """
        try:
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
        except ApiException as exc:
            logger.error(
                "Plaid link token creation failed for user %s: %s",
                user_id,
                exc,
                exc_info=True,
            )
            raise
        except Exception as exc:
            logger.exception("Unexpected error creating link token for user %s: %s",
                             user_id,
                             exc
            )
            raise

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
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)
            return response
        except ApiException as exc:
            logger.error(
                "Plaid public token exchange failed: %s", exc, exc_info=True
            )
            raise
        except Exception as exc:
            logger.exception("Unexpected error exchanging public token: %s", exc)
            raise

    def get_accounts(self, access_token: str) -> List[Account]:
        """
        Fetch accounts associated with a given access token.

        Args:
            access_token (str): Plaid access token for the user.

        Returns:
            List[Account]: List of Account domain models.

        Raises:
            ApiException: If the Plaid API call fails.
            Exception: For any unexpected errors.
        """
        try:
            request = AccountsBalanceGetRequest(access_token=access_token)
            res = self.client.accounts_balance_get(request)
            accounts = []
            for acc in res.accounts:
                try:
                    accounts.append(
                        Account(
                            id=acc.account_id,
                            name=acc.name,
                            type=parse_account_type(acc.type),
                            subtype=parse_account_subtype(acc.subtype),
                            balance=acc.balances.current,
                        )
                    )
                except (AttributeError, TypeError) as exc:
                    logger.exception(
                        "Failed to map Plaid account %s: %s",
                        getattr(acc, "account_id", None),
                        exc,
                    )
            return accounts
        except ApiException as exc:
            logger.error("Failed to fetch Plaid accounts: %s", exc, exc_info=True)
            raise
        except Exception as exc:
            logger.exception("Unexpected error fetching Plaid accounts")
            raise

    def get_transactions(
        self, access_token: str, start_date: str, end_date: str
    ) -> List[Transaction]:
        """
        Fetch transactions for an account within a specified date range.

        Args:
            access_token (str): Plaid access token for the user.
            start_date (str): Start date (YYYY-MM-DD) for transactions.
            end_date (str): End date (YYYY-MM-DD) for transactions.

        Returns:
            List[Transaction]: List of mapped Transaction domain models.

        Raises:
            ApiException: If the Plaid API call fails.
            Exception: For any unexpected errors.
        """
        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
            )
            res = self.client.transactions_get(request)
            transactions = [self.map_plaid_transaction(txn) for txn in res.transactions]
            return self.sort_transactions(transactions)
        except ApiException as exc:
            logger.error(
                "Failed to fetch Plaid transactions for dates %s to %s: %s",
                start_date,
                end_date,
                exc,
                exc_info=True,
            )
            raise
        except Exception as exc:
            logger.exception("Unexpected error fetching Plaid transactions: %s", exc)
            raise

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
        has_more = True
        added: List[Transaction] = []
        modified: List[Transaction] = []
        removed: List[str] = []

        try:
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
        except ApiException as exc:
            logger.error("Plaid transactions sync failed: %s", exc, exc_info=True)
            raise
        except Exception as exc:
            logger.exception("Unexpected error during transactions sync: %s", exc)
            raise

    def sort_transactions(self, txns: List[Transaction]) -> List[Transaction]:
        """
        Sort transactions deterministically by date and transaction ID.

        Args:
            txns (List[Transaction]): List of Transaction objects.

        Returns:
            List[Transaction]: Sorted list of transactions.

        Raises:
            Exception: If sorting fails.
        """
        try:
            return sorted(txns, key=lambda t: (t.date, t.transaction_id))
        except Exception as exc:
            logger.exception("Failed to sort transactions: %s", exc)
            raise

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
        try:
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
                category_confidence_level=getattr(pfc, "confidence_level", None)
                                         if pfc else None,
                pending=getattr(txn, "pending", None),
                iso_currency_code=getattr(txn, "iso_currency_code", None),
                unofficial_currency_code=getattr(txn, "unofficial_currency_code", None),
            )
        except Exception as exc:
            logger.exception(
                "Failed to map Plaid transaction %s: %s",
                getattr(txn, "transaction_id", None)
                , exc
            )
            raise
