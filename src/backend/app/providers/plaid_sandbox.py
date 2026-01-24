"""
Plaid sandbox integration implementing the BankingProvider interface.
"""

import os
from typing import List

from plaid import ApiClient, ApiException, Configuration
from plaid.api import plaid_api
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest
)
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest

from app.models.account import Account, parse_account_type, parse_account_subtype
from app.models.transaction import Transaction
from app.interfaces.banking_provider import BankingProvider
from app.logger import logger


class PlaidSandbox(BankingProvider):
    """
    Plaid sandbox implementation for testing account and transaction APIs.
    """
    name: str = "plaid"

    def __init__(self):
        """
        Initialize the Plaid API client using sandbox credentials.
        """
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
            user_id: The unique ID of the user.

        Returns:
            A link token string.
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

    def exchange_public_token(self, public_token: str) -> str:
        """
        Exchange a public token for an access token.

        Args:
            public_token: Public token returned by Plaid link.

        Returns:
            Access token string.
        """
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)
            return response.access_token
        except ApiException as exc:
            logger.error("Plaid public token exchange failed: %s", exc, exc_info=True)
            raise

    def get_accounts(self, access_token: str) -> List[Account]:
        """
        Fetch accounts for a given access token.

        Args:
            access_token: Plaid access token.

        Returns:
            A list of Account domain models.
        """
        try:
            request = AccountsBalanceGetRequest(access_token=access_token)
            res = self.client.accounts_balance_get(request)
            return [
                Account(
                    id=acc.account_id,
                    name=acc.name,
                    type=parse_account_type(acc.type),
                    subtype=parse_account_subtype(acc.subtype),
                    balance=acc.balances.current,
                )
                for acc in res.accounts
            ]
        except ApiException as exc:
            logger.error("Failed to fetch Plaid accounts: %s", exc, exc_info=True)
            raise

    def get_transactions(
        self, access_token: str, start_date: str, end_date: str
    ) -> List[Transaction]:
        """
        Fetch transactions for an account over a date range.

        Args:
            access_token: Plaid access token.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.

        Returns:
            A list of Transaction domain models.
        """
        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
            )
            res = self.client.transactions_get(request)

            transactions: List[Transaction] = []
            for txn in res.transactions:
                pfc = getattr(txn, "personal_finance_category", None)

                transactions.append(
                    Transaction(
                        transaction_id=txn.transaction_id,
                        account_id=txn.account_id,
                        name=txn.name,
                        merchant_name=getattr(txn, "merchant_name", None),
                        amount=txn.amount,
                        date=txn.date,
                        category_primary=getattr(pfc, "primary", None) if pfc else None,
                        category_detailed=getattr(pfc, "detailed", None) if pfc else None,
                        category_confidence_level=getattr(pfc, "confidence_level", None) if pfc else None,
                        pending=getattr(txn, "pending", None),
                        iso_currency_code=getattr(txn, "iso_currency_code", None),
                        unofficial_currency_code=getattr(txn, "unofficial_currency_code", None),
                    )
                )

            return transactions
        except ApiException as exc:
            logger.error(
                "Failed to fetch Plaid transactions for dates %s: %s to %s",
                start_date,
                end_date,
                exc,
                exc_info=True,
            )
            raise
