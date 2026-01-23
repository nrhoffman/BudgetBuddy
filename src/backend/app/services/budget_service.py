from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.logger import logger
from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.account_repository import AccountRepository


class BudgetService:
    def __init__(
        self,
        session: Session,
        user_repo: UserRepository,
        account_repo: AccountRepository,
        banking_provider=None,
    ):
        self.session = session
        self.user_repo = user_repo
        self.account_repo = account_repo
        self.banking_provider = banking_provider

    # ------------------------------
    # Auth
    # ------------------------------
    def login(self, username: str, password: str) -> dict:
        logger.info(f"Login attempt for username={username}")
        user = self.user_repo.get_by_username(username)

        if not user or not verify_password(password, user.hashed_password):
            logger.warning(f"Invalid login attempt for username={username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        token = create_access_token(subject=user.id)
        logger.info(f"User {user.id} logged in successfully")
        return {
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
        }

    # ------------------------------
    # User operations
    # ------------------------------
    def create_user(self, user: User):
        try:
            self.user_repo.add(user)
            logger.info(f"User created: id={user.id}, username={user.username}")
            return {"message": "User created successfully", "user_id": user.id}

        except IntegrityError as e:
            self.session.rollback()
            if "users_email_key" in str(e.orig):
                logger.warning(f"User creation failed: email conflict for {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists",
                )
            if "users_username_key" in str(e.orig):
                logger.warning(f"User creation failed: username conflict for {user.username}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists",
                )
            logger.warning(f"User creation failed: integrity error for {user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user data",
            )

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Unexpected DB error creating user {user.username}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )

    def get_user(self, user_id: str) -> User:
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                logger.warning(f"User not found: user_id={user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            logger.info(f"Fetched user {user_id}")
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user",
            )

    # ------------------------------
    # Account operations
    # ------------------------------
    def create_account(self, account: Account, user_id: str):
        try:
            self.account_repo.add_account(account, user_id)
            logger.info(f"Account created: account_id={account.id}, user_id={user_id}")
            return {"message": "Account created", "account_id": account.id}

        except SQLAlchemyError as e:
            logger.error(f"Failed to create account for user {user_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create account",
            )

    def get_account(self, account_id: str, user_id: str) -> Account:
        try:
            account = self.account_repo.get(account_id, user_id)
            if not account:
                logger.warning(f"Account not found: account_id={account_id}, user_id={user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found",
                )
            logger.info(f"Fetched account: account_id={account_id}, user_id={user_id}")
            return account
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching account {account_id} for user {user_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch account",
            )

    def remove_account(self, account_id: str, user_id: str):
        try:
            self.account_repo.delete_account(account_id, user_id)
            logger.info(f"Account {account_id} deleted for user {user_id}")
            return {"message": "Account deleted successfully"}
        except ValueError as ve:
            logger.warning(f"Attempted to delete non-existing account {account_id}: {ve}")
            raise HTTPException(status_code=404, detail=str(ve))
        except Exception as e:
            logger.error(f"Failed to delete account {account_id} for user {user_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to delete account")

    # ------------------------------
    # Transaction operations
    # ------------------------------
    def add_transaction(self, user_id: str, account_id: str, transaction: Transaction):
        try:
            account = self.account_repo.get(account_id, user_id)
            if not account:
                logger.warning(f"Transaction failed: account not found (account_id={account_id}, user_id={user_id})")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found",
                )

            self.account_repo.add_transaction(account_id, transaction, user_id)
            account.transactions.append(transaction)
            logger.info(f"Transaction added: transaction_id={transaction.transaction_id}, account_id={account_id}, user_id={user_id}")
            return {"message": "Transaction added", "transaction_id": transaction.transaction_id}

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"DB error adding transaction {transaction.transaction_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add transaction",
            )

    # ------------------------------
    # Fetch operations
    # ------------------------------

    def get_user_financial_snapshot(self, user_id: str) -> list[Account]:
        try:
            accounts = self.account_repo.get_all_accounts_with_transactions(user_id)
            logger.info(f"Fetched financial snapshot for user {user_id}")
            return accounts
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch financial snapshot for user {user_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch financial snapshot",
            )

    # ------------------------------
    # Banking / Plaid operations
    # ------------------------------
    def create_bank_link_token(self, user_id: str):
        if not self.banking_provider:
            logger.error("Banking provider not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Banking provider not configured",
            )

        logger.info(f"Creating bank link token for user {user_id}")
        return self.banking_provider.create_link_token(user_id)

    def add_bank_accounts(self, user_id: str, public_token: str):
        if not self.banking_provider:
            logger.error("Banking provider not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Banking provider not configured",
            )

        try:
            access_token = self.banking_provider.exchange_public_token(public_token)
            accounts = self.banking_provider.get_accounts(access_token)

            end_date = datetime.today().date()
            start_date = end_date - timedelta(days=90)

            total_transactions = 0

            for acc in accounts:
                self.create_account(acc, user_id)

                try:
                    transactions = self.banking_provider.get_transactions(
                        access_token=access_token,
                        start_date=start_date,
                        end_date=end_date
                    )
                    for txn in transactions:
                        self.add_transaction(user_id=user_id, account_id=acc.id, transaction=txn)

                    total_transactions += len(transactions)
                    logger.info(f"Account {acc.id} linked with {len(transactions)} transactions")

                except Exception as txn_err:
                    logger.error(f"Failed to fetch/add transactions for account {acc.id}: {txn_err}", exc_info=True)

            logger.info(f"Linked {len(accounts)} bank accounts for user {user_id}")
            return {"status": "linked", "accounts_added": len(accounts)}

        except Exception as e:
            logger.error(f"Failed to link bank accounts for user {user_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to link bank accounts",
            )
