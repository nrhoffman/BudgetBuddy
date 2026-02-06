"""
Repository layer for managing transactions in the database.

Provides methods to fetch, bulk upsert, and delete transactions, with
exception handling and logging.
"""

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.db.account_orm import AccountORM
from app.db.transaction_orm import TransactionORM
from app.models.transaction import Transaction
from app.mappers.account_mapper import orm_to_domain_transaction
from app.logger import logger


class TransactionRepository:
    """
    Repository for database operations on transactions.

    Supports fetching by ID, bulk upsert, and deletion for a user's transactions.
    All operations include SQLAlchemy exception handling and rollback safety.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a database session.

        Args:
            session (Session): Active SQLAlchemy session.
        """
        self.session = session

    # ---------------------------
    # Fetch methods
    # ---------------------------
    def get_by_ids(self, transaction_ids: list[str]) -> list[Transaction]:
        """
        Fetch transactions by a list of IDs.

        Args:
            transaction_ids (list[str]): List of transaction IDs.

        Returns:
            list[Transaction]: Mapped domain transaction objects.

        Raises:
            RuntimeError: If the database query fails.
        """
        try:
            orms = (
                self.session.query(TransactionORM)
                .filter(TransactionORM.id.in_(transaction_ids))
                .all()
            )
            return [orm_to_domain_transaction(orm) for orm in orms]

        except SQLAlchemyError as exc:
            logger.exception(
                "Failed to fetch transactions %s: %s",
                transaction_ids,
                exc
            )
            raise RuntimeError("Failed to fetch transactions") from exc

    # ---------------------------
    # Upsert methods
    # ---------------------------
    def bulk_upsert(self, user_id: str, transactions: list[Transaction]) -> int:
        """
        Bulk insert or update transactions for a user.

        Args:
            user_id (str): ID of the user.
            transactions (list[Transaction]): list of domain transactions.

        Returns:
            int: Number of rows inserted or updated.

        Raises:
            RuntimeError: If the bulk operation fails.
        """
        if not transactions:
            logger.debug(
                "No transactions provided for bulk upsert for user %s",
                user_id
            )
            return 0

        try:
            values = [
                {
                    "id": tx.transaction_id,
                    "account_id": tx.account_id,
                    "amount": abs(tx.amount),
                    "date": tx.date,
                    "balance_after": tx.balance_after,
                    "name": tx.name,
                    "merchant_name": tx.merchant_name,
                    "category_primary": tx.category_primary,
                    "category_detailed": tx.category_detailed,
                    "category_confidence_level": tx.category_confidence_level,
                    "pending": tx.pending,
                    "iso_currency_code": tx.iso_currency_code,
                    "unofficial_currency_code": tx.unofficial_currency_code,
                }
                for tx in transactions
            ]

            stmt = insert(TransactionORM).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=[TransactionORM.id],
                set_={
                    "amount": stmt.excluded.amount,
                    "date": stmt.excluded.date,
                    "balance_after": stmt.excluded.balance_after,
                    "name": stmt.excluded.name,
                    "merchant_name": stmt.excluded.merchant_name,
                    "category_primary": stmt.excluded.category_primary,
                    "category_detailed": stmt.excluded.category_detailed,
                    "category_confidence_level":
                        stmt.excluded.category_confidence_level,
                    "pending": stmt.excluded.pending,
                    "iso_currency_code": stmt.excluded.iso_currency_code,
                    "unofficial_currency_code": stmt.excluded.unofficial_currency_code,
                },
            )

            result = self.session.execute(stmt)
            self.session.commit()
            rowcount = result.rowcount or 0
            logger.debug("Bulk upserted %d transactions for user %s", rowcount, user_id)
            return rowcount

        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.exception("Bulk upsert failed for user %s", user_id)
            raise RuntimeError(f"Failed bulk upsert for user {user_id}: {exc}") from exc

    # ---------------------------
    # Delete methods
    # ---------------------------
    def delete_by_ids(self, user_id: str, transaction_ids: list[str]) -> int:
        """
        Delete multiple transactions belonging to a user.

        Args:
            user_id (str): ID of the user.
            transaction_ids (list[str]): List of transaction IDs to delete.

        Returns:
            int: Number of deleted rows.

        Raises:
            RuntimeError: If deletion fails.
        """
        if not transaction_ids:
            logger.debug(
                "No transaction IDs provided for deletion for user %s",
                user_id
            )
            return 0

        try:
            deleted_count = (
                self.session.query(TransactionORM)
                .join(AccountORM, TransactionORM.account_id == AccountORM.id)
                .filter(
                    AccountORM.user_id == user_id,
                    TransactionORM.id.in_(transaction_ids),
                )
                .delete(synchronize_session=False)
            )
            self.session.commit()
            logger.debug("Deleted %d transactions for user %s", deleted_count, user_id)
            return deleted_count

        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.exception(
                "Failed to delete transactions for user %s: %s",
                user_id,
                transaction_ids
            )
            raise RuntimeError(
                f"Failed to delete transactions for user {user_id}: {transaction_ids}"
            ) from exc
