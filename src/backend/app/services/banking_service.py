"""
Banking service layer.

Provides high-level banking operations including institution linking,
account synchronization, transaction retrieval, and webhook handling.
Coordinates external banking providers with internal persistence layers
using structured logging and domain-specific exception handling.
"""

import base64
from pathlib import Path
from typing import Optional, Any

from app.logger import logger
from app.tasks.plaid import sync_transactions
from app.models.exchange_token import ExchangeToken
from app.models.account import Account
from app.models.raw_provider_data import RawProviderData, Identity
from app.models.banking_service_deps import BankingServiceDependencies
from app.db.bank_item_token_orm import BankItemTokenORM
from app.exceptions import (
    AppError,
    BankingProviderError,
    ConflictError,
    DatabaseError,
    ValidationError,
    ExternalServiceError,
)


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
INSTITUTIONS_DIR = STATIC_DIR / "institutions"


class BankingService:
    """
    Service layer for banking-related operations.

    This service manages the lifecycle of bank institutions, accounts,
    and transactions by coordinating between external banking providers
    and internal repositories and services.
    """

    def __init__(self, deps: BankingServiceDependencies):
        self.banking_deps = deps

    # ---------------------------
    # Bank link token
    # ---------------------------
    def create_bank_link_token(self, user_id: str) -> dict[str, str]:
        """
        Create a bank link token for initiating account linking.

        Args:
            user_id (str): Identifier of the user requesting the link token.

        Returns:
            dict[str, str]: Provider-specific link token payload.

        Raises:
            ExternalServiceError: If the banking provider is not configured
                or token creation fails.
        """
        provider = self._require_provider()

        try:
            logger.info("Creating bank link token for user %s", user_id)
            return provider.create_link_token(user_id)
        except Exception as exc:
            logger.exception("Failed to create link token for user %s", user_id)
            raise ExternalServiceError("Failed to create link token") from exc
    
    def create_bank_update_link_token(
            self,
            user_id: str,
            institution_id: str
        ) -> dict[str, str]:
        provider = self._require_provider()

        token = self._get_token_by_user_id(
            user_id=user_id,
            institution_id=institution_id
        )

        try:
            logger.info("Creating bank update link token for user %s", user_id)
            return provider.create_update_link_token(
                user_id=user_id,
                access_token=token.access_token
            )
        except Exception as exc:
            logger.exception("Failed to create update link token for user %s", user_id)
            raise ExternalServiceError("Failed to create link token") from exc

    # ---------------------------
    # Bank account linking
    # ---------------------------
    def add_bank_institution(
        self,
        user_id: str,
        public_token: str,
        institution_id: Optional[str] = None,
        institution_name: Optional[str] = None,
    ) -> None:
        """
        Link a new bank institution and synchronize its accounts
        and transactions.

        Exchanges a public token for an access token, persists institution
        metadata, creates accounts, and applies recent transactions.

        Args:
            user_id (str): Identifier of the user linking the institution.
            public_token (str): Temporary public token from the provider.
            institution_id (Optional[str]): Provider institution identifier.
            institution_name (Optional[str]): Human-readable institution name.

        Raises:
            ConflictError: If the institution is already linked.
            ExternalServiceError: If provider interaction or syncing fails.
        """
        provider = self._require_provider()

        try:
            exchange_result = (
                provider.exchange_public_token(
                    public_token
                )
            )

            # Check if the institution is already linked
            if self.banking_deps.bank_repo.get_by_user(user_id, institution_id):
                raise ConflictError("Bank institution already linked")

            institution_logo = self.get_institution_logo(
                user_id,
                institution_id,
                exchange_result.item_id
            )

            self.banking_deps.bank_repo.save_token(
                user_id=user_id,
                provider="plaid",
                item_id=exchange_result.item_id,
                exchange_token=ExchangeToken(
                    public_token=exchange_result.access_token,
                    institution_id=institution_id,
                    institution_name=institution_name,
                    institution_logo=institution_logo
                ),
            )

            acc_res = provider.get_accounts(
                exchange_result.access_token,
                institution_id=institution_id,
                institution_logo=institution_logo
            )

            if not acc_res:
                logger.info(
                    "No accounts returned from provider for user %s",
                    user_id
                )
                return

            self._persist_raw(
                endpoint="accounts_balance_get",
                payload=acc_res.get("raw_pages"),
                user_id=user_id,
                item_id=exchange_result.item_id
            )

            self._create_accounts(
                user_id=user_id,
                accounts=acc_res.get("accounts"),
            )

            self._create_transactions(
                user_id=user_id,
                provider=provider,
                exchange_result=exchange_result,
                accounts=acc_res.get("accounts"),
            )

        except ConflictError:
            raise
        except Exception as exc:
            logger.exception("Failed to link bank accounts for user %s", user_id)
            raise ExternalServiceError("Failed to link bank accounts") from exc

    def sync_bank_accounts(
            self,
            user_id: str,
            institution_id: Optional[str] = None
    ) -> int:
        """
        Synchronize newly added bank accounts for an existing institution.

        Args:
            user_id (str): Identifier of the user.
            institution_id (Optional[str]): Institution to sync accounts for.

        Returns:
            int: Number of newly created accounts.

        Raises:
            ValidationError: If no bank token exists for the user.
            DatabaseError: If retrieving the bank token fails.
            ExternalServiceError: If provider synchronization fails.
        """
        provider = self._require_provider()

        token = self._get_token_by_user_id(
            user_id=user_id,
            institution_id=institution_id
        )

        plaid_res = provider.get_accounts(
            token.access_token,
            institution_id=institution_id,
            institution_logo=token.institution_logo
        )
        self._persist_raw(
            endpoint="accounts_balance_get",
            payload=plaid_res.get("raw_pages"),
            user_id=user_id,
            item_id=token.item_id
        )
        plaid_accs = plaid_res.get("accounts")

        db_accs = self.banking_deps.account_service.account_repo.get_all_accounts(
            user_id=user_id,
            institution_id=institution_id
        )

        plaid_map = {acc.id: acc for acc in plaid_accs}
        db_map = {acc.id: acc for acc in db_accs}

        created_count = 0

        # Create or undelete
        for plaid_id, plaid_acc in plaid_map.items():
            if plaid_id in db_map:
                db_acc = db_map[plaid_id]

                # Undelete if soft deleted
                if db_acc.deleted_at is not None:
                    self.banking_deps.account_service.account_repo.undelete_account(
                        account_id=db_acc.id,
                        user_id=user_id
                    )
            
            else:
                # New Account
                self.banking_deps.account_service.create_account(
                    account=plaid_acc,
                    user_id=user_id
                )
                created_count += 1

        for db_id, db_acc in db_map.items():
            if db_id not in plaid_map:
                self.banking_deps.account_service.account_repo.delete_account(
                    account_id=db_acc.id,
                    user_id=user_id
                )

        cursor = self.banking_deps.bank_repo.get_cursor_by_item_id(
            item_id=token.item_id
        )

        updated_db_accounts = (
            self.banking_deps.account_service.account_repo.get_all_accounts(
            user_id=user_id,
            institution_id=institution_id
            )
        )  

        self._create_transactions(
            user_id=user_id,
            provider=provider,
            exchange_result=token,
            accounts=updated_db_accounts,
            cursor=cursor.cursor
        )

        return created_count

    # ---------------------------
    # Plaid webhook
    # ---------------------------
    def plaid_webhook(self, payload: dict[str, Any]) -> None:
        """
        Handle incoming Plaid webhook events.

        Args:
            payload (dict[str, Any]): Raw webhook payload from the provider.
        """
        logger.info("Received Plaid webhook", extra={"payload": payload})

        self._persist_raw(
            endpoint="webhook",
            payload=payload
        )

        webhook_type = payload.get("webhook_type")
        webhook_code = payload.get("webhook_code")
        item_id = payload.get("item_id")

        if webhook_type != "TRANSACTIONS" or webhook_code not in {
            "SYNC_UPDATES_AVAILABLE", "INITIAL_UPDATE"
        }:
            logger.info(
                "Ignoring webhook type %s / code %s",
                webhook_type,
                webhook_code
            )
            return

        self.enqueue_plaid_sync(item_id)

    def enqueue_plaid_sync(self, item_id: str) -> None:
        """
        Enqueue a background task to synchronize transactions.

        Args:
            item_id (str): Provider item identifier to sync.
        """
        logger.info("Queuing Plaid sync for item_id: %s", item_id)
        sync_transactions.delay(item_id)

    # ---------------------------
    # Utilities
    # ---------------------------
    def get_institution_logo(self, user_id: str,
                             institution_id: str,
                             item_id: str
    ) -> str:
        """
        Fetch the institution's logo from the banking provider, save it locally as a
        PNG, and return a URL path that can be accessed by the frontend.

        The logo is retrieved as a base64-encoded string from the provider, decoded to
        bytes, and stored under `static/institutions/<institution_id>.png`. The raw
        provider response is also logged in the database for auditing and traceability.

        Args:
            user_id (str): The ID of the user associated with this institution.
                institution_id (str): The unique identifier of the institution.
            item_id (str): The Plaid item ID corresponding to the user's linked
                account.

        Returns:
            str: Relative URL path to the saved logo
                (e.g., "/static/institutions/ins_123.png"), or None if no logo was found
                for the institution.

        Side Effects:
            - Creates `static/institutions/` directory if it does not exist.
            - Writes the logo PNG file to disk.
            - Persists the raw provider response via `raw_provider_repo.save` for
            auditing.
        """

        institution = self._fetch_institution(institution_id)

        self._persist_raw(
            endpoint="get_institution_by_id",
            payload=institution,
            user_id=user_id,
            item_id=item_id
        )

        logo_base64 = institution.get("logo")

        if not logo_base64:
            return None

        try:
            logo_bytes = base64.b64decode("".join(logo_base64.split()))
        except Exception as exc:
            raise ValidationError(
                "Invalid base64 logo data returned by banking provider",
                details={"institution_id": institution_id},
            ) from exc

        INSTITUTIONS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = INSTITUTIONS_DIR / f"{institution_id}.png"

        try:
            with open(file_path, "wb") as f:
                f.write(logo_bytes)
        except OSError as exc:
            raise AppError(
                "Failed to write institution logo to disk",
                details={
                    "institution_id": institution_id,
                    "path": str(file_path),
                },
            ) from exc

        return f"/static/institutions/{institution_id}.png"

    def _require_provider(self):
        if not self.banking_deps.banking_provider:
            logger.error("Banking provider not configured")
            raise ExternalServiceError("Banking provider not configured")
        return self.banking_deps.banking_provider

    def _persist_raw(
        self,
        endpoint: str,
        payload: Any,
        user_id: str | None = None,
        item_id: str | None = None,
    ):
        try:
            self.banking_deps.raw_provider_repo.save(
                RawProviderData(
                    provider="plaid",
                    endpoint=endpoint,
                    payload=payload,
                    identity=Identity(user_id=user_id, item_id=item_id)
                    if user_id or item_id
                    else None,
                )
            )
        except Exception as exc:
            raise DatabaseError(
                "Failed to persist raw provider response",
                details={"endpoint": endpoint},
            ) from exc
    
    def _get_token_by_user_id(self, user_id: str, institution_id: str) -> BankItemTokenORM:
        try:
            token = self.banking_deps.bank_repo.get_by_user(user_id, institution_id)
        except Exception as exc:
            logger.exception(
                "Database error retrieving bank token for user %s",
                user_id
            )
            raise DatabaseError("Failed to retrieve bank token") from exc
        if not token:
            raise ValidationError("No bank token found for user")
        
        return token
    
    def _create_accounts(
        self,
        user_id: str,
        accounts: list[Account]
    ) -> int:
        created_count = 0
        for account in accounts:
            self.banking_deps.account_service.create_account(account, user_id)
            created_count += 1
        
        return created_count

    def _create_transactions(
        self,
        user_id: str,
        provider: Any,
        exchange_result: BankItemTokenORM,
        accounts: list[Account],
        cursor: str | None = None,
    ):
        txn_res = provider.get_transactions_sync(
            exchange_result.access_token,
            accounts=accounts,
            cursor=cursor
        )

        self._persist_raw(
            endpoint="transactions_sync",
            payload=txn_res.get("raw_pages", []),
            user_id=user_id,
            item_id=exchange_result.item_id
        )
        
        self.banking_deps.account_service.apply_transaction_changes(
            user_id=user_id,
            added=txn_res.get("added", []),
            modified=txn_res.get("modified", []),
            removed=txn_res.get("removed", []),
        )

        self.banking_deps.bank_repo.save_cursor(
            user_id=user_id,
            item_id=exchange_result.item_id,
            cursor=txn_res.get("next_cursor")
        )

    def _fetch_institution(self, institution_id: str) -> dict:
        try:
            return self.banking_deps.banking_provider.get_institution_by_id(
                institution_id=institution_id
            )
        except Exception as exc:
            raise BankingProviderError(
                "Failed to retrieve institution from provider",
                details={"institution_id": institution_id},
            ) from exc
