"""
Celery task for syncing transactions from Plaid sandbox.

This task synchronizes transactions for a given banking item, fetching updates
from Plaid and applying them via AccountService with structured error handling.
"""

from datetime import datetime, timezone
from typing import Optional
from app.celery_app import celery_app
from app.logger import logger
from app.db.session import SESSIONLOCAL
from app.repositories.bank_repository import BankRepository
from app.models.raw_provider_data import RawProviderData, Identity, Cursor
from app.models.account import Account
from app.db.bank_item_token_orm import BankItemTokenORM
from app.services.account_service import AccountService
from app.providers.plaid_sandbox import PlaidSandbox
from app.exceptions import DatabaseError, ExternalServiceError, ValidationError
from app.tasks.helpers import build_plaid_sync_context


@celery_app.task(bind=True, name="app.tasks.plaid.sync_transactions")
def sync_transactions(_task, item_id: str) -> None:
    """
    Background task to synchronize transactions for a Plaid item.

    This task fetches transaction updates from Plaid for the given item,
    applies the changes to user accounts via AccountService, and updates
    the sync cursor. It handles errors with structured logging and raises
    appropriate exceptions if external or database operations fail.

    Steps:
        1. Initialize repositories and services.
        2. Fetch the access token for the Plaid item.
        3. Retrieve the last sync cursor (if any).
        4. Fetch transaction updates from Plaid.
        5. Apply transaction changes (added, modified, removed).
        6. Save the updated cursor.
        7. Close the database session.

    Args:
        _task: Celery task instance (unused, required by bind=True).
        item_id (str): Identifier of the Plaid item to sync.

    Raises:
        ValidationError: If transaction data fails validation.
        DatabaseError: If any database operation fails (e.g., save
        cursor, apply transactions).
        ExternalServiceError: If communication with Plaid or other
        external service fails.
    """
    logger.info("Starting transaction sync for item_id: %s", item_id)
    db = SESSIONLOCAL()

    try:
        ctx = build_plaid_sync_context(db)

        token = _fetch_access_token(ctx.bank_repo, item_id)

        accounts = ctx.account_repo.get_all_accounts_with_transactions(token.user_id)

        cursor_record = ctx.bank_repo.get_cursor_by_item_id(item_id)
        cursor: Optional[str] = cursor_record.cursor if cursor_record else None

        sync_result = _fetch_transactions(
            ctx.plaid,
            token.access_token,
            accounts,
            cursor)

        sync_res_model = RawProviderData(
            provider="plaid",
            endpoint="transactions_sync",
            payload=sync_result.get("raw"),
            identity=Identity(user_id=token.user_id, item_id=item_id),
            cursor=Cursor(
                before=cursor,
                after=sync_result.get("next_cursor")
            ),
            occurred_at=datetime.now(timezone.utc),
        )

        ctx.raw_provider_repo.save(sync_res_model)

        # Log first added/modified for debug
        if added := sync_result.get("added"):
            logger.debug("First added transaction: %s", added[0])
        if modified := sync_result.get("modified"):
            logger.debug("First modified transaction: %s", modified[0])

        _apply_transactions(ctx.account_service, token, sync_result)

        _save_cursor(
            ctx.bank_repo,
            token.user_id,
            item_id,
            sync_result.get("next_cursor")
        )

        logger.info("Transaction sync completed successfully for item_id: %s", item_id)

    except (DatabaseError, ExternalServiceError, ValidationError):
        raise
    except Exception as exc:
        logger.exception(
            "Unexpected error during transaction sync for item_id: %s",
            item_id
        )
        raise ExternalServiceError("Unexpected error during transaction sync") from exc
    finally:
        db.close()
        logger.debug("Database session closed for item_id: %s", item_id)


def _fetch_access_token(bank_repo: BankRepository, item_id: str) -> BankItemTokenORM:
    """
    Retrieve the access token for a given Plaid item.

    Args:
        bank_repo (BankRepository): Repository for bank tokens.
        item_id (str): Identifier of the Plaid item.

    Returns:
        The access token associated with the item.

    Raises:
        ExternalServiceError: If no token is found for the item.
    """

    token = bank_repo.get_token_by_item_id(item_id)
    if not token:
        logger.warning("No access token found for item_id: %s", item_id)
        raise ExternalServiceError(f"No access token found for item_id: {item_id}")
    return token


def _fetch_transactions(
        plaid: PlaidSandbox,
        access_token: str,
        accounts: list[Account],
        cursor: Optional[str]
) -> dict:
    """
    Fetch transaction updates from Plaid using the sync endpoint.

    Args:
        plaid (PlaidSandbox): Plaid sandbox provider instance.
        access_token (str): Plaid access token for the item.
        accounts (list[Account]): List of accounts for access_token
        cursor (Optional[str]): Cursor to fetch incremental updates.

    Returns:
        dict: Dictionary containing 'added', 'modified', 'removed', and 'next_cursor'.

    Raises:
        ExternalServiceError: If fetching transactions from Plaid fails.
    """

    try:
        return plaid.get_transactions_sync(access_token, accounts, cursor)
    except Exception as exc:
        logger.exception("Plaid sync failed for access token")
        raise ExternalServiceError("Failed to fetch transactions from Plaid") from exc


def _apply_transactions(
        account_service: AccountService,
        token,
        sync_result: dict
) -> None:
    """
    Apply transaction changes to the user's accounts via AccountService.

    Args:
        account_service (AccountService): Service responsible for
        accounts/transactions.
        token: Bank token object containing user_id and access token.
        sync_result (dict): Transaction data from Plaid with keys 'added',
        'modified', 'removed'.

    Raises:
        ValidationError: If transaction data fails validation.
        DatabaseError: If applying transactions to the database fails.
        ExternalServiceError: For unexpected errors applying transactions.
    """

    try:
        account_service.apply_transaction_changes(
            user_id=token.user_id,
            added=sync_result.get("added", []),
            modified=sync_result.get("modified", []),
            removed=sync_result.get("removed", []),
        )
    except ValidationError as exc:
        logger.warning(
            "Validation error applying transactions for user %s: %s",
            token.user_id, exc
        )
        raise
    except DatabaseError as exc:
        logger.error(
            "Database error applying transactions for user %s: %s",
            token.user_id, exc, exc_info=True
        )
        raise
    except Exception as exc:
        logger.exception(
            "Unexpected error applying transactions for user %s",
            token.user_id
        )
        raise ExternalServiceError("Failed to apply transactions") from exc


def _save_cursor(
        bank_repo: BankRepository,
        user_id: str,
        item_id: str,
        next_cursor: Optional[str]
) -> None:
    """
    Save the updated sync cursor for a Plaid item.

    Args:
        bank_repo (BankRepository): Repository for bank tokens/cursors.
        user_id (str): ID of the user associated with the item.
        item_id (str): Plaid item ID.
        next_cursor (Optional[str]): Cursor to save for incremental updates.

    Raises:
        DatabaseError: If saving the cursor to the database fails.
    """

    if next_cursor:
        try:
            bank_repo.save_cursor(
                user_id=user_id,
                item_id=item_id,
                cursor=next_cursor
            )
            logger.debug("Next cursor saved: %s", next_cursor)
        except Exception as exc:
            logger.error(
                "Failed to save cursor for item_id %s: %s",
                item_id, exc, exc_info=True
            )
            raise DatabaseError("Failed to save sync cursor") from exc
