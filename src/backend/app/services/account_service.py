"""
Account service layer.

Contains business logic for managing user financial accounts and their
associated transactions. Coordinates persistence through repositories
and ensures consistent balance recalculation using centralized
exception handling and structured logging.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from app.logger import logger
from app.models.account import Account, UpdateAccount
from app.models.transaction import Transaction, UpdateTransaction
from app.repositories.account_repository import AccountRepository
from app.repositories.bank_repository import BankRepository
from app.repositories.transaction_repository import TransactionRepository
from app.exceptions import DatabaseError, NotFoundError, ValidationError


class AccountService:
    """
    Service responsible for managing user accounts and transactions.

    Provides account CRUD operations, transaction updates, balance
    recalculation, and institution lookups while enforcing ownership
    and consistency rules.
    """

    def __init__(
        self,
        account_repo: AccountRepository,
        bank_repo: BankRepository,
        txn_repo: TransactionRepository,
    ):
        self.account_repo = account_repo
        self.bank_repo = bank_repo
        self.txn_repo = txn_repo

    # ---------------------------
    # Account operations
    # ---------------------------
    def create_account(self, account: Account, user_id: str) -> dict[str, str]:
        """
        Create a new financial account for a user.

        Args:
            account (Account): Account model to persist.
            user_id (str): Identifier of the owning user.

        Returns:
            dict[str, str]: Confirmation payload containing account ID.

        Raises:
            DatabaseError: If account persistence fails.
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
            raise DatabaseError("Failed to create account") from exc

    def get_account(self, account_id: str, user_id: str) -> Account:
        """
        Retrieve a single account owned by a user.

        Args:
            account_id (str): Identifier of the account.
            user_id (str): Identifier of the owning user.

        Returns:
            Account: Retrieved account model.

        Raises:
            NotFoundError: If the account does not exist.
            DatabaseError: If retrieval fails.
        """

        try:
            account = self.account_repo.get(account_id, user_id)
            if not account:
                logger.warning(
                    "Account not found: account_id=%s, user_id=%s",
                    account_id,
                    user_id
                )
                raise NotFoundError("Account not found")
            logger.info(
                "Fetched account: account_id=%s, user_id=%s",
                account_id,
                user_id
            )
            return account
        except NotFoundError:
            raise
        except Exception as exc:
            logger.error(
                "Error fetching account %s for user %s: %s",
                account_id,
                user_id,
                exc,
                exc_info=True
            )
            raise DatabaseError("Failed to fetch account") from exc

    def update_account(
        self,
        account_id: str,
        user_id: str,
        payload: Optional[UpdateAccount] = None,
        balance: Optional[float] = None,
    ) -> None:
        """
        Update mutable fields of an existing account.

        Args:
            account_id (str): Identifier of the account.
            user_id (str): Identifier of the owning user.
            payload (UpdateAccount): Partial account update payload.
            balance (Optional[float]): Updated balance.

        Raises:
            ValidationError: If no fields are provided for update.
            NotFoundError: If the account does not exist.
            DatabaseError: If the update fails.
        """

        account_name = payload.account_name if payload else None
        apr = payload.apr if payload else None

        if all(value is None for value in (account_name, balance, apr)):
            raise ValidationError("No fields provided to update")

        try:
            self.account_repo.update_account(
                account_id=account_id,
                user_id=user_id,
                payload=payload,
                balance=balance,
            )
            logger.info(
                "Account updated: account_id=%s, user_id=%s",
                account_id,
                user_id
            )
        except ValueError as exc:
            logger.warning(str(exc))
            raise NotFoundError(str(exc)) from exc
        except Exception as exc:
            logger.error(
                "Error updating account %s for user %s: %s",
                account_id,
                user_id, exc,
                exc_info=True
            )
            raise DatabaseError("Failed to update account") from exc

    def remove_account(self, account_id: str, user_id: str) -> None:
        """
        Delete an account owned by a user.

        Args:
            account_id (str): Identifier of the account.
            user_id (str): Identifier of the owning user.

        Raises:
            NotFoundError: If the account does not exist.
            DatabaseError: If deletion fails.
        """

        try:
            self.account_repo.delete_account(account_id, user_id)
            logger.info(
                "Account deleted: account_id=%s, user_id=%s",
                account_id,
                user_id
            )
        except ValueError as exc:
            logger.warning(
                "Attempted to delete non-existing account %s: %s",
                account_id,
                exc
            )
            raise NotFoundError(str(exc)) from exc
        except Exception as exc:
            logger.error(
                "Failed to delete account %s for user %s: %s",
                account_id,
                user_id, exc,
                exc_info=True
            )
            raise DatabaseError("Failed to delete account") from exc

    def undelete_accounts(self, institution_id: str, user_id: str) -> int:
        """
        Undelete all soft-deleted accounts for a given institution and user.

        Args:
            institution_id (str): The institution ID.
            user_id (str): The user ID.

        Returns:
            int: Number of accounts that were undeleted.
        """
        try:
            undeleted_count = self.account_repo.undelete_accounts(
                institution_id,
                user_id
            )
            return undeleted_count
        except Exception as e:

            self.logger.error(
                "Failed to undelete accounts for user %s and institution %s: %s",
                user_id,
                institution_id,
                str(e),
            )
            raise

    # ---------------------------
    # Transaction operations
    # ---------------------------
    def update_transaction(
        self,
        user_id: str,
        account_id: str,
        transaction_id: str,
        payload: UpdateTransaction,
    ) -> None:
        """
        Update a single transaction and rebalance affected accounts.

        Args:
            user_id (str): Identifier of the owning user.
            account_id (str): Identifier of the associated account.
            transaction_id (str): Identifier of the transaction.
            payload (UpdateTransaction): Partial transaction update payload.

        Raises:
            NotFoundError: If the transaction does not exist or does not
                belong to the account.
            DatabaseError: If the update fails.
        """

        existing_tx_list = self.txn_repo.get_by_ids([transaction_id])
        if not existing_tx_list:
            logger.warning(
                "Transaction %s not found for user %s",
                transaction_id,
                user_id
            )
            raise NotFoundError("Transaction not found")

        try:
            existing_tx = existing_tx_list[0]
            if existing_tx.account_id != account_id:
                logger.warning(
                    "Transaction %s does not belong to account %s for user %s",
                    transaction_id,
                    account_id,
                    user_id
                )
                raise NotFoundError("Transaction not found")

            updated_tx = existing_tx.model_copy(
                update=payload.model_dump(exclude_unset=True)
            )
            self.apply_transaction_changes(
                user_id=user_id,
                added=[],
                modified=[updated_tx],
                removed=[]
            )
            logger.info(
                "Updated transaction %s for account %s, user %s",
                transaction_id,
                account_id,
                user_id
            )
        except Exception as exc:
            logger.exception(
                "Failed to update transaction %s for account %s, user %s: %s",
                transaction_id,
                account_id,
                user_id,
                exc
            )
            raise DatabaseError("Failed to update transaction") from exc

    def apply_transaction_changes(
        self,
        *,
        user_id: str,
        added: list[Transaction],
        modified: list[Transaction],
        removed: list[str],
    ) -> None:
        """
        Apply transaction changes and rebalance affected accounts.

        Args:
            user_id (str): Identifier of the owning user.
            added (list[Transaction]): Newly added transactions.
            modified (list[Transaction]): Updated transactions.
            removed (list[str]): IDs of removed transactions.
        """

        self._remove_transactions(user_id, removed)
        self._upsert_transactions(added)
        self._upsert_transactions(modified)
        boundaries = self.find_earliest_dates(user_id, added, modified, removed)
        self._rebalance_accounts(user_id, boundaries)

    def _remove_transactions(self, user_id: str, txn_ids: list[str]) -> None:
        """
        Remove transactions by ID.

        Args:
            user_id (str): Identifier of the owning user.
            txn_ids (list[str]): Transaction IDs to delete.
        """

        if txn_ids:
            self.txn_repo.delete_by_ids(user_id, txn_ids)

    def _upsert_transactions(self, txns: list[Transaction]) -> None:
        """
        Insert or update transactions in bulk.

        Args:
            txns (list[Transaction]): Transactions to upsert.
        """

        if txns:
            self.txn_repo.bulk_upsert(txns)

    def _rebalance_accounts(
            self,
            user_id: str,
            from_dates: dict[str, dict[str, datetime]]
    ) -> None:
        """
        Recalculate account balances from affected transaction dates.

        Args:
            user_id (str): Identifier of the owning user.
            from_dates (dict): Boundary dates per account.
        """

        self.account_repo.recalculate_balances_from(user_id, from_dates)

    def find_earliest_dates(
        self,
        user_id: str,
        added: list[Transaction],
        modified: list[Transaction],
        removed: list[str],
    ) -> dict[str, dict[str, Optional[datetime]]]:
        """
        Determine transaction boundary dates for balance recalculation.

        Args:
            user_id (str): Identifier of the owning user.
            added (list[Transaction]): Newly added transactions.
            modified (list[Transaction]): Modified transactions.
            removed (list[str]): Removed transaction IDs.

        Returns:
            dict[str, dict[str, Optional[datetime]]]: Per-account date boundaries.
        """

        boundaries: dict[str, dict[str, Optional[datetime]]] = {}
        txn_ids = {t.transaction_id for t in modified} | set(removed)
        old_txns = {
            tx.transaction_id: tx for tx in self.txn_repo.get_by_ids(list(txn_ids))
        } if txn_ids else {}

        def update_boundary(
                account_id: str,
                tx_date: datetime,
                import_date: Optional[datetime]
        ):
            """
            Update transaction date boundaries for balance recalculation.

            Determines whether a transaction occurred before or after the
            account's initial import completion date and updates the
            appropriate boundary for the given account.

            Args:
                account_id (str): Identifier of the affected account.
                tx_date (datetime): Transaction date to evaluate.
                import_date (Optional[datetime]): Initial import completion date
                    for the account.
            """
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

        for t in added + modified:
            account = self.account_repo.get(t.account_id, user_id)
            old_tx = old_txns.get(t.transaction_id)
            if old_tx:
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
    # Institution operations
    # ---------------------------
    def get_institutions(self, user_id: str) -> list[dict]:
        """
        Retrieve all linked banking institutions for a user.

        Args:
            user_id (str): Identifier of the user.

        Returns:
            list[dict]: List of institution metadata associated with the user.

        Raises:
            DatabaseError: If fetching institutions fails.
        """

        try:
            institutions = self.bank_repo.get_institutions(user_id)
            logger.info("Fetched institutions for user %s", user_id)
            return institutions
        except SQLAlchemyError as exc:
            logger.error(
                "Failed to fetch institutions for user %s: %s",
                user_id,
                exc,
                exc_info=True
            )
            raise DatabaseError("Failed to fetch institutions") from exc

    # ---------------------------
    # User financial snapshot
    # ---------------------------
    def get_user_financial_snapshot(self, user_id: str) -> list[Account]:
        """
        Retrieve a complete financial snapshot for a user.

        Includes all accounts and their associated transactions.

        Args:
            user_id (str): Identifier of the user.

        Returns:
            list[Account]: User accounts populated with transactions.

        Raises:
            DatabaseError: If fetching the financial snapshot fails.
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
            raise DatabaseError("Failed to fetch financial snapshot") from exc
