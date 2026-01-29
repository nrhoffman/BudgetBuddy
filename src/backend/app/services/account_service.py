"""
Account service layer.

This module contains business logic for managing user financial accounts
and their associated transactions. It coordinates persistence through
the account repository and enforces application-level validation and
error
"""

from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.logger import logger
from app.models.account import Account
from app.models.transaction import Transaction, UpdateTransaction
from app.repositories.account_repository import AccountRepository


class AccountService:
    """
    Service responsible for managing user accounts and transactions.
    """

    def __init__(self, account_repo: AccountRepository):
        """
        Initialize the account service.

        Args:
            account_repo: Repository for account and transaction persistence.
        """
        self.account_repo = account_repo

    def create_account(self, account: Account, user_id: str) -> dict:
        """
        Create a new financial account for a user.

        Args:
            account: Account model instance to persist.
            user_id: Identifier of the owning user.

        Returns:
            dict: Confirmation message and created account identifier.

        Raises:
            HTTPException: If account creation fails.
        """
        try:
            self.account_repo.add_account(account, user_id)
            logger.info(
                "Account created successfully: account_id=%s, user_id=%s",
                account.id,
                user_id,
            )
            return {
                "message": "Account created",
                "account_id": account.id,
            }

        except SQLAlchemyError as exc:
            logger.error(
                "Failed to create account for user %s: %s",
                user_id,
                exc,
                exc_info=True,
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
            Account: Account instance if found.

        Raises:
            HTTPException: If account is not found or retrieval fails.
        """
        try:
            account = self.account_repo.get(account_id, user_id)
            if not account:
                logger.warning(
                    "Account not found: account_id=%s, user_id=%s",
                    account_id,
                    user_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found",
                )

            logger.info(
                "Fetched account successfully: account_id=%s, user_id=%s",
                account_id,
                user_id,
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
                exc_info=True,
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
    ) -> dict:
        """
        Update one or more fields on a user's account.

        Partial updates are supported; only provided fields are modified.

        Args:
            account_id: Identifier of the account to update.
            user_id: Identifier of the owning user.
            account_name: Optional updated account name.
            balance: Optional updated account balance.

        Returns:
            dict: Confirmation message.

        Raises:
            HTTPException:
                - 400 if no update fields are provided
                - 404 if the account does not exist
                - 500 for unexpected server errors
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
                balance=balance,
            )

            logger.info(
                "Account updated successfully: account_id=%s, user_id=%s",
                account_id,
                user_id,
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
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update account",
            ) from exc

    def remove_account(self, account_id: str, user_id: str) -> dict:
        """
        Delete an account belonging to a user.

        Args:
            account_id: Identifier of the account.
            user_id: Identifier of the owning user.

        Returns:
            dict: Confirmation message.

        Raises:
            HTTPException: If deletion fails or account is not found.
        """
        try:
            self.account_repo.delete_account(account_id, user_id)
            logger.info(
                "Account deleted successfully: account_id=%s, user_id=%s",
                account_id,
                user_id,
            )
            return {"message": "Account deleted successfully"}

        except ValueError as exc:
            logger.warning(
                "Attempted to delete non-existing account %s: %s",
                account_id,
                exc,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        except Exception as exc:
            logger.error(
                "Failed to delete account %s for user %s: %s",
                account_id,
                user_id,
                exc,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete account",
            ) from exc

    # ------------------------------------------------------------------
    # Transaction operations
    # ------------------------------------------------------------------
    def add_transaction(
        self,
        user_id: str,
        account_id: str,
        transaction: Transaction,
    ) -> dict:
        """
        Add a transaction to a user's account.

        Args:
            user_id: Identifier of the owning user.
            account_id: Identifier of the account.
            transaction: Transaction model instance to persist.

        Returns:
            dict: Confirmation message and transaction identifier.

        Raises:
            HTTPException: If account is not found or a DB error occurs.
        """
        try:
            account = self.account_repo.get(account_id, user_id)
            if not account:
                logger.warning(
                    "Transaction failed: account not found "
                    "(account_id=%s, user_id=%s)",
                    account_id,
                    user_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found",
                )

            self.account_repo.add_transaction(account_id, transaction, user_id)
            account.transactions.append(transaction)

            logger.info(
                "Transaction added successfully: transaction_id=%s, account_id=%s",
                transaction.transaction_id,
                account_id,
            )
            return {
                "message": "Transaction added",
                "transaction_id": transaction.transaction_id,
            }

        except SQLAlchemyError as exc:
            logger.error(
                "Database error adding transaction %s: %s",
                transaction.transaction_id,
                exc,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add transaction",
            ) from exc
        
    def update_transaction(
        self,
        user_id: str,
        account_id: str,
        transaction_id: str,
        transaction: UpdateTransaction,
    ) -> dict:
        """
        Update editable fields on an existing transaction.

        Args:
            user_id: Identifier of the owning user.
            account_id: Identifier of the account.
            transaction_id: Identifier of the transaction to update.
            transaction: UpdateTransaction payload containing fields to update.

        Returns:
            dict: Confirmation message and transaction identifier.

        Raises:
            HTTPException: If account or transaction is not found,
                           or if a DB error occurs.
        """
        try:
            account = self.account_repo.get(account_id, user_id)
            if not account:
                logger.warning(
                    "Transaction update failed: account not found "
                    "(account_id=%s, user_id=%s)",
                    account_id,
                    user_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found",
                )

            existing_tx = next(
                (tx for tx in account.transactions
                 if tx.transaction_id == transaction_id),
                None,
            )

            if not existing_tx:
                logger.warning(
                    "Transaction update failed: transaction not found "
                    "(transaction_id=%s, account_id=%s)",
                    transaction_id,
                    account_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found",
                )

            update_data = transaction.model_dump(exclude_unset=True)
            if not update_data:
                return {
                    "message": "No updates applied",
                    "transaction_id": transaction_id,
                }

            if any(field in update_data for field in ("category_primary",
                                                      "category_detailed")
            ):
                update_data["category_confidence_level"] = "MANUAL"

            old_primary = existing_tx.category_primary
            new_primary = update_data.get("category_primary", old_primary)
            old_is_income = self.is_income(old_primary)
            new_is_income = self.is_income(new_primary)
            is_credit_loan = self.is_credit_loan(account.type)

            if is_credit_loan:
                old_is_income, new_is_income = not old_is_income, not new_is_income

            if old_is_income == new_is_income:
                balance_delta = Decimal("0")
            else:
                amount = existing_tx.amount
                if old_is_income and not new_is_income:
                    balance_delta = -Decimal("2") * amount
                else:
                    balance_delta = Decimal("2") * amount

            self.account_repo.update_transaction(
                account_id=account_id,
                transaction_id=transaction_id,
                user_id=user_id,
                updates={
                    **update_data,
                    "balance_after": existing_tx.balance_after + balance_delta,
                },
            )

            if balance_delta != 0:
                self.account_repo.rebalance_transactions_after(
                    account_id=account_id,
                    after_date=existing_tx.date,
                    delta=balance_delta,
                    include_original=existing_tx
                )

            for field, value in update_data.items():
                setattr(existing_tx, field, value)

            logger.info(
                "Transaction updated successfully: transaction_id=%s, account_id=%s",
                transaction_id,
                account_id,
            )

            return {
                "message": "Transaction updated",
                "transaction_id": transaction_id,
            }

        except SQLAlchemyError as exc:
            logger.error(
                "Database error updating transaction %s: %s",
                transaction_id,
                exc,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update transaction",
            ) from exc

    def get_user_financial_snapshot(self, user_id: str) -> list[Account]:
        """
        Retrieve all accounts and transactions for a user.

        Args:
            user_id: Identifier of the user.

        Returns:
            list[Account]: Accounts with associated transactions.

        Raises:
            HTTPException: If a database error occurs.
        """
        try:
            accounts = self.account_repo.get_all_accounts_with_transactions(
                user_id,
            )
            logger.info(
                "Fetched financial snapshot successfully for user %s",
                user_id,
            )
            return accounts

        except SQLAlchemyError as exc:
            logger.error(
                "Failed to fetch financial snapshot for user %s: %s",
                user_id,
                exc,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch financial snapshot",
            ) from exc

    def is_income(self, category_primary: str | None) -> bool:
        return category_primary in ["INCOME", "TRANSFER_IN"]
    
    def is_credit_loan(self, account_type: str | None) -> bool:
        return account_type in ["credit", "loan"]
