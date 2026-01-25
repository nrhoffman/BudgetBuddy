"""
Repository layer for accounts and transactions.
"""

from typing import List, Optional

from sqlalchemy.orm import joinedload, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert

from app.db.account_orm import AccountORM
from app.db.transaction_orm import TransactionORM
from app.mappers.account_mapper import orm_to_domain_account
from app.models.account import Account
from app.models.transaction import Transaction


class AccountRepository:
    """
    Repository for managing accounts and their transactions in the database.
    """

    def __init__(self, session: Session):
        """
        Initialize repository with a SQLAlchemy session.

        Args:
            session: SQLAlchemy Session instance.
        """
        self.session = session

    def get(self, account_id: str, user_id: str) -> Account:
        """
        Fetch a single account for a user by account ID.

        Args:
            account_id: ID of the account.
            user_id: ID of the user.

        Returns:
            Account domain model.

        Raises:
            ValueError if account not found.
            RuntimeError if database error occurs.
        """
        try:
            orm = (
                self.session.query(AccountORM)
                .filter(AccountORM.id == account_id, AccountORM.user_id == user_id)
                .first()
            )
            if not orm:
                raise ValueError(f"Account {account_id} not found for user {user_id}")
            return orm_to_domain_account(orm)
        except SQLAlchemyError as exc:
            raise RuntimeError(
                f"Failed to fetch account {account_id} for user {user_id}"
            ) from exc

    def add_account(self, account: Account, user_id: str) -> None:
        """
        Add a new account for a user.

        Args:
            account: Account domain model to add.
            user_id: ID of the user.

        Raises:
            RuntimeError if database commit fails.
        """
        try:
            orm = AccountORM(
                id=account.id,
                name=account.name,
                type=account.type,
                balance=account.balance,
                user_id=user_id,
            )
            self.session.add(orm)
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise RuntimeError(
                f"Failed to add account {account.id} for user {user_id}"
            ) from exc

    def delete_account(self, account_id: str, user_id: str) -> None:
        """
        Delete a user's account by ID.

        Args:
            account_id: ID of the account to delete.
            user_id: ID of the user.

        Raises:
            ValueError if account not found.
            RuntimeError if deletion fails.
        """
        try:
            orm = (
                self.session.query(AccountORM)
                .filter(AccountORM.id == account_id, AccountORM.user_id == user_id)
                .first()
            )
            if not orm:
                raise ValueError(f"Account {account_id} not found for user {user_id}")

            self.session.delete(orm)
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            raise RuntimeError(
                f"Failed to delete account {account_id} for user {user_id}"
            ) from exc

    def add_transaction(self, account_id: str, tx: Transaction, user_id: str) -> None:
        """
        Add or update a transaction for a given account.

        Args:
            account_id: ID of the account.
            tx: Transaction domain model.
            user_id: ID of the user.

        Raises:
            ValueError if account not found.
            RuntimeError if database commit fails.
        """
        try:
            account_orm = (
                self.session.query(AccountORM)
                .filter(AccountORM.id == account_id, AccountORM.user_id == user_id)
                .first()
            )
            if not account_orm:
                raise ValueError(f"Account {account_id} not found for user {user_id}")

            self.upsert_transaction(self.session, tx, account_id)
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise RuntimeError(
                f"Failed to add transaction {tx.transaction_id} to account {account_id}"
            ) from exc

    def upsert_transaction(self, session: Session, tx: Transaction, account_id: str):
        """
        Insert or update a transaction using PostgreSQL upsert.

        Args:
            session: SQLAlchemy session.
            tx: Transaction domain model.
            account_id: ID of the account.
        """
        stmt = insert(TransactionORM).values(
            id=tx.transaction_id,
            account_id=account_id,
            amount=tx.amount,
            date=tx.date,
            name=tx.name,
            merchant_name=tx.merchant_name,
            category_primary=tx.category_primary,
            category_detailed=tx.category_detailed,
            category_confidence_level=tx.category_confidence_level,
            pending=tx.pending,
            iso_currency_code=tx.iso_currency_code,
            unofficial_currency_code=tx.unofficial_currency_code,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=[TransactionORM.id],
            set_={
                "amount": stmt.excluded.amount,
                "date": stmt.excluded.date,
                "name": stmt.excluded.name,
                "merchant_name": stmt.excluded.merchant_name,
                "category_primary": stmt.excluded.category_primary,
                "category_detailed": stmt.excluded.category_detailed,
                "category_confidence_level": stmt.excluded.category_confidence_level,
                "pending": stmt.excluded.pending,
                "iso_currency_code": stmt.excluded.iso_currency_code,
                "unofficial_currency_code": stmt.excluded.unofficial_currency_code,
            },
        )
        session.execute(stmt)

    def update_account(
        self,
        account_id: str,
        user_id: str,
        account_name: Optional[str] = None,
        balance: Optional[float] = None,
    ) -> dict:
        """
        Update an existing account.

        Args:
            account_id: ID of the account to update.
            user_id: ID of the user.
            account_name: Optional new name for the account.
            balance: Optional new balance for the account.

        Raises:
            ValueError: If the account does not exist.
            RuntimeError: If the update fails.
        """
        try:
            orm = (
                self.session.query(AccountORM)
                .filter(
                    AccountORM.id == account_id,
                    AccountORM.user_id == user_id
                )
                .first()
            )

            if not orm:
                raise ValueError(f"Account {account_id} not found for user {user_id}")

            if account_name is not None:
                orm.name = account_name
            if balance is not None:
                orm.balance = balance

            self.session.commit()
            self.session.refresh(orm)

        except ValueError:
            self.session.rollback()
            raise

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise RuntimeError(
                f"Failed to update account {account_id} for user {user_id}"
            ) from exc

    def get_all_accounts_with_transactions(self, user_id: str) -> List[Account]:
        """
        Fetch all accounts with transactions for a user.

        Args:
            user_id: ID of the user.

        Returns:
            List of Account domain models.

        Raises:
            RuntimeError if query fails.
        """
        try:
            orms = (
                self.session.query(AccountORM)
                .filter(AccountORM.user_id == user_id)
                .options(joinedload(AccountORM.transactions))
                .all()
            )
            return [orm_to_domain_account(orm) for orm in orms]
        except SQLAlchemyError as exc:
            raise RuntimeError(
                f"Failed to fetch accounts with transactions for user {user_id}"
            ) from exc
