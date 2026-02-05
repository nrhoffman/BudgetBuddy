"""
Account service layer.

This module contains business logic for managing user financial accounts
and their associated transactions. It coordinates persistence through
the account repository and enforces application-level validation and error handling.
"""

from datetime import datetime
from typing import Optional, List, Dict
from fastapi import HTTPException, status

from sqlalchemy.exc import SQLAlchemyError

from app.logger import logger
from app.models.account import Account
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository


class AccountService:
    """
    Service responsible for managing user accounts and transactions.
    """

    def __init__(
        self,
        account_repo: AccountRepository,
        txn_repo: TransactionRepository,
    ):
        """
        Initialize the account service.

        Args:
            account_repo: Repository for account and transaction persistence.
            txn_repo: Repository for transaction persistence.
        """
        self.account_repo = account_repo
        self.txn_repo = txn_repo

    # ---------------------------
    # Account operations
    # ---------------------------
    def create_account(self, account: Account, user_id: str) -> Dict[str, str]:
        """
        Create a new financial account for a user.

        Args:
            account: Account model instance to persist.
            user_id: Identifier of the owning user.

        Returns:
            Dict with confirmation message and created account ID.

        Raises:
            HTTPException: If account creation fails.
        """
        try:
            self.account_repo.add_account(account, user_id)
            logger.info(
                "Account created: account_id=%s, user_id=%s",
                account.id,
                user_id
            )
            return {"message": "Account created", "account_id": account.id}

        except SQLAlchemyError as exc:
            logger.error(
                "Failed to create account for user %s: %s",
                user_id,
                exc,
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create account",
            ) from exc

    def get_account(self, account_id: str, user_id: str) -> Account:
        """
        Retrieve a specific account for a user.

        Args:
            account_id: Identifier of the account.
            user_id: Identifier of the owning user.

        Returns:
            Account instance.

        Raises:
            HTTPException: 404 if account not found, 500 if retrieval fails.
        """
        try:
            account = self.account_repo.get(account_id, user_id)
            if not account:
                logger.warning(
                    "Account not found: account_id=%s, user_id=%s",
                    account_id,
                    user_id
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found"
                )

            logger.info(
                "Fetched account: account_id=%s, user_id=%s",
                account_id,
                user_id
            )
            return account

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(
                "Error fetching account %s for user %s: %s",
                account_id,
                user_id,
                exc,
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch account",
            ) from exc

    def update_account(
        self,
        account_id: str,
        user_id: str,
        account_name: Optional[str] = None,
        balance: Optional[float] = None,
    ) -> Dict[str, str]:
        """
        Update one or more fields of a user's account.

        Args:
            account_id: Account ID to update.
            user_id: Owner of the account.
            account_name: Optional new account name.
            balance: Optional new account balance.

        Returns:
            Dict with confirmation message.

        Raises:
            HTTPException: 400 if no fields, 500 if update fails.
        """
        if account_name is None and balance is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided to update",
            )

        try:
            self.account_repo.update_account(
                account_id=account_id,
                user_id=user_id,
                account_name=account_name,
                balance=balance
            )
            logger.info(
                "Account updated: account_id=%s, user_id=%s",
                account_id,
                user_id
            )
            return {"message": "Account updated successfully"}

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(
                "Error updating account %s for user %s: %s",
                account_id,
                user_id,
                exc,
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update account",
            ) from exc

    def remove_account(self, account_id: str, user_id: str) -> Dict[str, str]:
        """
        Delete a user's account.

        Args:
            account_id: ID of the account to delete.
            user_id: Owner of the account.

        Returns:
            Dict with confirmation message.

        Raises:
            HTTPException: 404 if account not found, 500 if deletion fails.
        """
        try:
            self.account_repo.delete_account(account_id, user_id)
            logger.info(
                "Account deleted: account_id=%s, user_id=%s",
                account_id,
                user_id
            )
            return {"message": "Account deleted successfully"}

        except ValueError as exc:
            logger.warning(
                "Attempted to delete non-existing account %s: %s",
                account_id,
                exc
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc)
            ) from exc
        except Exception as exc:
            logger.error(
                "Failed to delete account %s for user %s: %s",
                account_id,
                user_id,
                exc,
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete account",
            ) from exc

    # ---------------------------
    # Transaction operations
    # ---------------------------
    def apply_transaction_changes(
        self,
        *,
        user_id: str,
        added: List[Transaction],
        modified: List[Transaction],
        removed: List[str],
    ) -> None:
        """
        Apply changes to user transactions: remove, add, and modify.

        Args:
            user_id: Owner of the transactions.
            added: Transactions to add.
            modified: Transactions to update.
            removed: Transaction IDs to remove.
        """
        self._remove_transactions(user_id, removed)
        self._upsert_transactions(user_id, added)
        self._upsert_transactions(user_id, modified)

        boundaries = self.find_earliest_dates(user_id, added, modified, removed)
        self._rebalance_accounts(user_id, boundaries)

    def _remove_transactions(self, user_id: str, txn_ids: List[str]) -> None:
        if txn_ids:
            self.txn_repo.delete_by_ids(user_id, txn_ids)

    def _upsert_transactions(self, user_id: str, txns: List[Transaction]) -> None:
        if txns:
            self.txn_repo.bulk_upsert(user_id, txns)

    def _rebalance_accounts(
            self,
            user_id: str,
            from_dates: Dict[str, Dict[str, datetime]]
    ) -> None:
        self.account_repo.recalculate_balances_from(user_id, from_dates)

    def find_earliest_dates(
        self,
        user_id: str,
        added: List[Transaction],
        modified: List[Transaction],
        removed: List[str],
    ) -> Dict[str, Dict[str, Optional[datetime]]]:
        """
        Determine earliest and latest transaction dates relative to
        account import.

        Returns:
            Dictionary keyed by account_id with 'latest_before_import'
            and 'earliest_after_import'.
        """
        boundaries: Dict[str, Dict[str, Optional[datetime]]] = {}
        txn_ids = {t.transaction_id for t in modified} | set(removed)
        old_txns = {
            tx.transaction_id: tx for tx in self.txn_repo.get_by_ids(list(txn_ids))
        } if txn_ids else {}

        def update_boundary(
                account_id: str,
                tx_date: datetime,
                import_date: Optional[datetime]
        ):
            if account_id not in boundaries:
                boundaries[account_id] = {
                    "latest_before_import": None,
                    "earliest_after_import": None
                }
            if import_date is None:
                import_date = datetime.min

            if tx_date.date() <= import_date.date():
                current = boundaries[account_id]["latest_before_import"]
                if current is None or tx_date > current:
                    boundaries[account_id]["latest_before_import"] = tx_date
            else:
                current = boundaries[account_id]["earliest_after_import"]
                if current is None or tx_date < current:
                    boundaries[account_id]["earliest_after_import"] = tx_date

        for t in added:
            account = self.account_repo.get(t.account_id, user_id)
            update_boundary(
                t.account_id,
                t.date,
                account.initial_import_completed_at
            )

        for t in modified:
            old_tx = old_txns.get(t.transaction_id)
            if old_tx:
                account = self.account_repo.get(t.account_id, user_id)
                update_boundary(
                    t.account_id,
                    old_tx.date,
                    account.initial_import_completed_at
                )
                update_boundary(
                    t.account_id,
                    t.date,
                    account.initial_import_completed_at
                )
            else:
                account = self.account_repo.get(t.account_id, user_id)
                update_boundary(
                    t.account_id,
                    t.date,
                    account.initial_import_completed_at
                )

        for txn_id in removed:
            old_tx = old_txns.get(txn_id)
            if old_tx:
                account = self.account_repo.get(old_tx.account_id, user_id)
                update_boundary(
                    old_tx.account_id,
                    old_tx.date,
                    account.initial_import_completed_at
                )

        return boundaries

    # ---------------------------
    # User financial snapshot
    # ---------------------------
    def get_user_financial_snapshot(self, user_id: str) -> List[Account]:
        """
        Retrieve all accounts and associated transactions for a user.

        Args:
            user_id: Identifier of the user.

        Returns:
            List of Account instances with transactions.

        Raises:
            HTTPException: If retrieval fails.
        """
        try:
            accounts = self.account_repo.get_all_accounts_with_transactions(user_id)
            logger.info("Fetched financial snapshot for user %s", user_id)
            return accounts

        except SQLAlchemyError as exc:
            logger.error(
                "Failed to fetch financial snapshot for user %s: %s",
                user_id,
                exc,
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch financial snapshot",
            ) from exc
