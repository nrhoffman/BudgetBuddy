"""
Repository layer for managing transactions in the database.

Provides methods to fetch, bulk upsert, and delete transactions
"""

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.db.account_orm import AccountORM
from app.db.transaction_orm import TransactionORM
from app.models.transaction import Transaction
from app.mappers.account_mapper import orm_to_domain_transaction


class TransactionRepository:
    """
    Repository for database operations on transactions.

    Supports fetching by ID, bulk upsert, and deletion for a user's transactions.
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
        """
        orms = (
            self.session.query(TransactionORM)
            .filter(TransactionORM.id.in_(transaction_ids))
            .all()
        )
        return [orm_to_domain_transaction(orm) for orm in orms]

    # ---------------------------
    # Upsert methods
    # ---------------------------
    def bulk_upsert(self, transactions: list[Transaction]) -> int:
        """
        Bulk insert or update transactions for a user.

        Args:
            user_id (str): ID of the user.
            transactions (list[Transaction]): list of domain transactions.

        Returns:
            int: Number of rows inserted or updated.
        """
        if not transactions:
            return 0

        values = [
            {
                "id": tx.transaction_id,
                "account_id": tx.account_id,
                "account_type": tx.account_type,
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
        rowcount = result.rowcount or 0
        return rowcount

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
        """
        if not transaction_ids:
            return 0

        deleted_count = (
            self.session.query(TransactionORM)
            .join(AccountORM, TransactionORM.account_id == AccountORM.id)
            .filter(
                AccountORM.user_id == user_id,
                TransactionORM.id.in_(transaction_ids),
            )
            .delete(synchronize_session=False)
        )
        return deleted_count
