"""
Budget service layer for the BudgetBuddy application.

This module defines the BudgetService class, which contains the core
business logic for authentication, user management, account handling,
transactions, and external banking provider integrations.
"""

from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.logger import logger
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.repositories.user_repository import UserRepository


class BudgetService:
    """
    Core application service coordinating repositories and external
    providers while enforcing business rules and error handling.
    """

    def __init__(
        self,
        session: Session,
        user_repo: UserRepository,
        account_repo: AccountRepository,
        banking_provider=None,
    ):
        """
        Initialize the BudgetService.

        Args:
            session: SQLAlchemy session for database operations.
            user_repo: Repository responsible for user persistence.
            account_repo: Repository responsible for account persistence.
            banking_provider: Optional external banking provider (e.g. Plaid).
        """
        self.session = session
        self.user_repo = user_repo
        self.account_repo = account_repo
        self.banking_provider = banking_provider

    # ------------------------------
    # Authentication
    # ------------------------------
    def login(self, username: str, password: str) -> dict:
        """
        Authenticate a user and issue an access token.

        Args:
            username: User's username.
            password: Plain-text password.

        Returns:
            Dictionary containing the access token and metadata.

        Raises:
            HTTPException: If authentication fails.
        """
        logger.info("Login attempt for username=%s", username)
        user = self.user_repo.get_by_username(username)

        if not user or not verify_password(password, user.hashed_password):
            logger.warning("Invalid login attempt for username=%s", username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        token = create_access_token(subject=user.id)
        logger.info("User %s logged in successfully", user.id)

        return {
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
        }

    # ------------------------------
    # User operations
    # ------------------------------
    def create_user(self, user: User) -> dict:
        """
        Create a new user.

        Args:
            user: User model to persist.

        Returns:
            Confirmation message and created user ID.

        Raises:
            HTTPException: If user creation fails.
        """
        try:
            self.user_repo.add(user)
            logger.info(
                "User created: id=%s, username=%s",
                user.id,
                user.username,
            )
            return {"message": "User created successfully", "user_id": user.id}

        except IntegrityError as exc:
            self.session.rollback()
            error_msg = str(exc.orig)

            if "users_email_key" in error_msg:
                logger.warning(
                    "User creation failed: email conflict for %s",
                    user.email,
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists",
                )

            if "users_username_key" in error_msg:
                logger.warning(
                    "User creation failed: username conflict for %s",
                    user.username,
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists",
                )

            logger.warning(
                "User creation failed due to integrity error: %s",
                user.username,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user data",
            )

        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.error(
                "Database error creating user %s: %s",
                user.username,
                exc,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )

    def get_user(self, user_id: str) -> User:
        """
        Retrieve a user by ID.

        Args:
            user_id: User identifier.

        Returns:
            User instance.

        Raises:
            HTTPException: If the user is not found or retrieval fails.
        """
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                logger.warning("User not found: user_id=%s", user_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            logger.info("Fetched user %s", user_id)
            return user

        except HTTPException:
            raise

        except Exception as exc:
            logger.error(
                "Error fetching user %s: %s",
                user_id,
                exc,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user",
            )

    # ------------------------------
    # Account operations
    # ------------------------------
    def create_account(self, account: Account, user_id: str) -> dict:
        """
        Create a new account for a user.

        Args:
            account: Account model to persist.
            user_id: Owning user ID.

        Returns:
            Confirmation message and account ID.
        """
        try:
            self.account_repo.add_account(account, user_id)
            logger.info(
                "Account created: account_id=%s, user_id=%s",
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
            )

    def get_account(self, account_id: str, user_id: str) -> Account:
        """
        Retrieve an account for a user.

        Args:
            account_id: Account identifier.
            user_id: Owning user identifier.

        Returns:
            Account instance.

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
                "Fetched account: account_id=%s, user_id=%s",
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
            )

    def remove_account(self, account_id: str, user_id: str) -> dict:
        """
        Remove an account for a user.

        Args:
            account_id: Account identifier.
            user_id: Owning user identifier.

        Returns:
            Confirmation message.
        """
        try:
            self.account_repo.delete_account(account_id, user_id)
            logger.info(
                "Account %s deleted for user %s",
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
            )

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
            )

    # ------------------------------
    # Transaction operations
    # ------------------------------
    def add_transaction(
        self,
        user_id: str,
        account_id: str,
        transaction: Transaction,
    ) -> dict:
        """
        Add a transaction to an account.

        Args:
            user_id: Owning user identifier.
            account_id: Account identifier.
            transaction: Transaction to add.

        Returns:
            Confirmation message and transaction ID.
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
                "Transaction added: transaction_id=%s, account_id=%s",
                transaction.transaction_id,
                account_id,
            )
            return {
                "message": "Transaction added",
                "transaction_id": transaction.transaction_id,
            }

        except HTTPException:
            raise

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
            )

    # ------------------------------
    # Fetch operations
    # ------------------------------
    def get_user_financial_snapshot(self, user_id: str) -> list[Account]:
        """
        Retrieve all accounts and transactions for a user.

        Args:
            user_id: User identifier.

        Returns:
            List of accounts with transactions.
        """
        try:
            accounts = self.account_repo.get_all_accounts_with_transactions(
                user_id
            )
            logger.info(
                "Fetched financial snapshot for user %s",
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
            )

    # ------------------------------
    # Banking / external provider operations
    # ------------------------------
    def create_bank_link_token(self, user_id: str) -> dict:
        """
        Create a bank link token for a user.

        Args:
            user_id: User identifier.

        Returns:
            Provider-specific link token.
        """
        if not self.banking_provider:
            logger.error("Banking provider not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Banking provider not configured",
            )

        logger.info("Creating bank link token for user %s", user_id)
        return self.banking_provider.create_link_token(user_id)

    def add_bank_accounts(self, user_id: str, public_token: str) -> dict:
        """
        Link bank accounts and import recent transactions.

        Args:
            user_id: User identifier.
            public_token: Public token from banking provider.

        Returns:
            Summary of linked accounts.
        """
        if not self.banking_provider:
            logger.error("Banking provider not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Banking provider not configured",
            )

        try:
            access_token = self.banking_provider.exchange_public_token(
                public_token
            )
            accounts = self.banking_provider.get_accounts(access_token)

            end_date = datetime.today().date()
            start_date = end_date - timedelta(days=90)

            for account in accounts:
                self.create_account(account, user_id)

                try:
                    transactions = self.banking_provider.get_transactions(
                        access_token=access_token,
                        start_date=start_date,
                        end_date=end_date,
                    )

                    for txn in transactions:
                        self.add_transaction(
                            user_id=user_id,
                            account_id=account.id,
                            transaction=txn,
                        )

                    logger.info(
                        "Account %s linked with %s transactions",
                        account.id,
                        len(transactions),
                    )

                except Exception as txn_err:
                    logger.error(
                        "Failed to add transactions for account %s: %s",
                        account.id,
                        txn_err,
                        exc_info=True,
                    )

            logger.info(
                "Linked %s bank accounts for user %s",
                len(accounts),
                user_id,
            )
            return {
                "status": "linked",
                "accounts_added": len(accounts),
            }

        except Exception as exc:
            logger.error(
                "Failed to link bank accounts for user %s: %s",
                user_id,
                exc,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to link bank accounts",
            )
