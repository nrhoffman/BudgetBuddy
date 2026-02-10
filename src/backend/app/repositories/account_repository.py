"""
Repository layer for accounts and transactions.

This module contains database access logic for user accounts and their
associated transactions. It is responsible for persistence, balance
recalculation, and maintaining transactional integrity.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.db.account_orm import AccountORM
from app.db.transaction_orm import TransactionORM
from app.mappers.account_mapper import orm_to_domain_account
from app.models.account import Account


class AccountRepository:
    """
    Repository for managing accounts and transactions.

    Encapsulates all database operations related to accounts, transactions,
    and balance recalculations using SQLAlchemy.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a database session.

        Args:
            session: Active SQLAlchemy session.
        """
        self.session = session

    # -----------------------
    # CRUD operations
    # -----------------------

    def get(self, account_id: str, user_id: str) -> Account:
        """
        Retrieve a single account belonging to a user.

        Args:
            account_id: Identifier of the account.
            user_id: Identifier of the owning user.

        Returns:
            Account domain model.

        Raises:
            ValueError: If the account does not exist.
        """
        orm = (
            self.session.query(AccountORM)
            .filter(
                AccountORM.id == account_id,
                AccountORM.user_id == user_id,
            )
            .first()
        )

        if not orm:
            raise ValueError(
                f"Account {account_id} not found for user {user_id}"
            )

        return orm_to_domain_account(orm)

    def add_account(self, account: Account, user_id: str) -> None:
        """
        Create a new account for a user.

        Args:
            account: Account domain model.
            user_id: Identifier of the owning user.
        """
        orm = AccountORM(
            id=account.id,
            name=account.name,
            type=account.type,
            subtype=account.subtype,
            balance=account.balance,
            initial_balance=account.balance,
            user_id=user_id,
        )
        self.session.add(orm)

    def update_account(
        self,
        account_id: str,
        user_id: str,
        account_name: Optional[str] = None,
        balance: Optional[float] = None,
    ) -> None:
        """
        Update account metadata.

        Args:
            account_id: Identifier of the account.
            user_id: Identifier of the owning user.
            account_name: Optional new account name.
            balance: Optional new account balance.

        Raises:
            ValueError: If the account does not exist.
        """
        orm = (
            self.session.query(AccountORM)
            .filter(
                AccountORM.id == account_id,
                AccountORM.user_id == user_id,
            )
            .first()
        )

        if not orm:
            raise ValueError(
                f"Account {account_id} not found for user {user_id}"
            )

        if account_name is not None:
            orm.name = account_name
        if balance is not None:
            orm.balance = balance

    def delete_account(self, account_id: str, user_id: str) -> None:
        """
        Delete an existing account.

        Args:
            account_id: Identifier of the account.
            user_id: Identifier of the owning user.

        Raises:
            ValueError: If the account does not exist.
        """
        orm = (
            self.session.query(AccountORM)
            .filter(
                AccountORM.id == account_id,
                AccountORM.user_id == user_id,
            )
            .first()
        )

        if not orm:
            raise ValueError(
                f"Account {account_id} not found for user {user_id}"
            )

        self.session.delete(orm)

    # -----------------------
    # Balance updates
    # -----------------------
    def recalculate_balances_from(
        self,
        user_id: str,
        boundary_dates: dict[str, dict[str, datetime]],
    ) -> None:
        """
        Recalculate balances for accounts from boundary dates.

        Args:
            user_id: Identifier of the user.
            boundary_dates: Mapping of account IDs to date boundaries.
        """
        for account_id, dates in boundary_dates.items():
            start_date = dates.get("latest_before_import")
            if start_date is not None:
                self.recalculate_balances_backward(user_id, account_id)

            # --- Post-import transactions (walk forward) ---
            start_date = dates.get("earliest_after_import")
            if start_date is not None:
                account = self.get(account_id, user_id)

                prev_tx = (
                    self.session.query(TransactionORM)
                    .join(AccountORM)
                    .filter(
                        TransactionORM.account_id == account_id,
                        TransactionORM.date > start_date,
                    )
                    .order_by(desc(TransactionORM.date))
                    .first()
                )

                if prev_tx is not None and prev_tx.balance_after is not None:
                    running_balance = Decimal(prev_tx.balance_after)
                else:
                    last_before_tx = (
                        self.session.query(TransactionORM)
                        .filter(TransactionORM.account_id == account_id)
                        .order_by(desc(TransactionORM.date))
                        .first()
                    )
                    running_balance = Decimal(
                        last_before_tx.balance_after or account.initial_balance or 0
                    )

                txs = (
                    self.session.query(TransactionORM)
                    .join(AccountORM)
                    .filter(
                        TransactionORM.account_id == account_id,
                        TransactionORM.date >= start_date,
                        AccountORM.user_id == user_id,
                    )
                    .order_by(TransactionORM.date)
                    .all()
                )

                for tx in txs:
                    running_balance += self.signed_amount(tx)
                    tx.balance_after = running_balance

                account.balance = running_balance

    def recalculate_balances_backward(
            self,
            user_id: str,
            account_id: str,
    ) -> None:
        """
        Recalculate historical balances for an account, walking backward from
        the initial import date.

        This method updates the `balance_after` field of all transactions
        that occurred on or before the account's initial import date. If no
        historical transactions exist, it sets the balance on the first
        transaction to the account's initial balance.

        Args:
            user_id: The ID of the user who owns the account.
            account_id: The ID of the account to recalculate.
        """
        account = self.get(account_id, user_id)
        initial_balance = account.initial_balance or Decimal("0")
        import_date = account.initial_import_completed_at.date()
        old_txs = (
            self.session.query(TransactionORM)
            .join(AccountORM)
            .filter(
                TransactionORM.account_id == account_id,
                TransactionORM.date <= import_date,
                AccountORM.user_id == user_id,
            )
            .order_by(desc(TransactionORM.date))
            .all()
        )

        if not old_txs:
            first_tx = (
                self.session.query(TransactionORM)
                .filter(TransactionORM.account_id == account_id)
                .order_by(TransactionORM.date)
                .first()
            )
            if first_tx:
                first_tx.balance_after = initial_balance or Decimal("0")
                old_txs = [first_tx]

        running_balance = Decimal(
            old_txs[0].balance_after or initial_balance or 0
        )
        for tx in old_txs:
            tx.balance_after = running_balance
            running_balance -= self.signed_amount(tx)

    # -----------------------
    # Utility methods
    # -----------------------

    def signed_amount(self, tx: TransactionORM) -> Decimal:
        """
        Return the signed amount of a transaction based on its direction.

        - 'in' transactions increase the balance.
        - 'out' transactions decrease the balance.

        Args:
            tx (TransactionORM): Transaction ORM instance with a 'direction' property.

        Returns:
            Decimal: Signed transaction amount.
        """
        amount = Decimal(tx.amount)
        return amount if tx.direction == "in" else -amount

    # -----------------------
    # Query helpers
    # -----------------------

    def get_all_accounts_with_transactions(
        self,
        user_id: str,
    ) -> list[Account]:
        """
        Retrieve all accounts and transactions for a user.

        Args:
            user_id: Identifier of the user.

        Returns:
            List of account domain models.
        """
        orms = (
            self.session.query(AccountORM)
            .filter(AccountORM.user_id == user_id)
            .options(joinedload(AccountORM.transactions))
            .all()
        )
        return [orm_to_domain_account(orm) for orm in orms]
