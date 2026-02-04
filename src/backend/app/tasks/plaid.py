"""
Celery task for syncing transactions from Plaid sandbox.

This module defines the background task to synchronize transactions for a
given banking item. It retrieves the access token and cursor from the
database, fetches updates from Plaid, and applies them via the
AccountService.
"""

from typing import Optional
from app.celery_app import celery_app
from app.logger import logger
from app.db.session import SESSIONLOCAL
from app.repositories.bank_repository import BankRepository
from app.services.account_service import AccountService
from app.providers.plaid_sandbox import PlaidSandbox


@celery_app.task(bind=True, name="app.tasks.plaid.sync_transactions")
def sync_transactions(self, item_id: str) -> None:
    """
    Synchronize transactions for a given Plaid item in the background.

    Args:
        item_id: Identifier of the Plaid item to sync.

    Behavior:
        - Fetches access token and cursor from the database.
        - Calls PlaidSandbox to retrieve added, modified, and removed transactions.
        - Updates transactions in AccountService.
        - Logs progress and warnings.
        - Ensures DB session is closed after processing.
    """
    logger.info("Starting transaction sync for item_id: %s", item_id)
    db = SESSIONLOCAL()

    try:
        bank_repo = BankRepository(db)
        account_service = AccountService(db)
        plaid = PlaidSandbox()

        token = bank_repo.get_token_by_item_id(item_id)
        if not token:
            logger.warning("No access token found for item_id: %s", item_id)
            return

        cursor_record = bank_repo.get_cursor_by_item_id(item_id)
        cursor: Optional[str] = cursor_record.cursor if cursor_record else None

        sync_result = plaid.get_transactions_sync(token.access_token, cursor)
        print(sync_result)

        # # Log first added transaction for debugging
        # if sync_result.get("added"):
        #     logger.info("First added transaction: %s", sync_result["added"][0])

        # # Apply added transactions
        # for txn in sync_result.get("added", []):
        #     account_service.apply_transaction_changes(token.user_id, txn.account_id, txn)

        # Uncomment if supporting modified/removed transactions
        # for txn in sync_result.get("modified", []):
        #     account_service.update_transaction(token.user_id, txn.account_id, txn)

        # for txn in sync_result.get("removed", []):
        #     account_service.remove_transaction(token.user_id, txn)

        # Save next cursor to database
        # bank_repo.save_cursor(user_id=token.user_id, item_id=item_id, cursor=sync_result["next_cursor"])

        logger.info("Transaction sync completed for item_id: %s", item_id)

    except Exception:
        logger.exception("Error syncing transactions for item_id: %s", item_id)
        raise

    finally:
        db.close()
        logger.debug("Database session closed for item_id: %s", item_id)
