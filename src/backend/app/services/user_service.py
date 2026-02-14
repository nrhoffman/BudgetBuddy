"""
User service module.

Provides business logic for managing user lifecycle operations,
including permanent deletion of user data and all associated
financial records across repositories.

This layer coordinates repository interactions and ensures
consistent error handling through domain-specific exceptions.
"""

from app.exceptions import DatabaseError
from app.logger import logger
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.repositories.bank_repository import BankRepository
from app.repositories.raw_provider_repository import RawProviderRepository
from app.repositories.user_repository import UserRepository

class UserService:
    """
    Service layer responsible for user-related business operations.

    Coordinates deletion of user-associated financial data across
    multiple repositories to ensure full data removal.
    """
    def __init__(
        self,
        account_repo: AccountRepository,
        bank_repo: BankRepository,
        raw_provider_repo: RawProviderRepository,
        user_repo: UserRepository
    ):
        """
        Initialize the UserService with required repositories.

        Args:
            account_repo (AccountRepository): Repository managing user accounts.
            bank_repo (BankRepository): Repository managing banking-related data.
            raw_provider_repo (RawProviderRepository): Repository managing raw 
            provider data.
            user_repo (UserRepository): Repository managing user records.
        """
        self.account_repo = account_repo
        self.bank_repo = bank_repo
        self.raw_provider_repo = raw_provider_repo
        self.user_repo = user_repo

    def delete_all(self, user: User) -> None:
        """
        Permanently delete a user and all associated financial data.

        This operation removes:
            - All accounts linked to the user
            - Banking integration data
            - Raw provider data
            - The user record itself

        Args:
            user (User): The user entity to be permanently deleted.

        Raises:
            DatabaseError: If any repository operation fails during deletion.
        """
        logger.warning("PERMANENT DELETE triggered for user_id=%s", user.id)

        try:
            self.account_repo.delete_all_accounts(user.id)
            logger.debug("Deleted accounts for user_id=%s", user.id)
            self.bank_repo.delete_banking_data(user.id)
            logger.debug("Deleted banking data for user_id=%s", user.id)
            self.raw_provider_repo.delete_all(user.id)
            logger.debug("Deleted raw data for user_id=%s", user.id)
            self.user_repo.delete(user.id)
            logger.debug("Deleted user data for user_id=%s", user.id)

            logger.info("Completed full data deletion for user_id=%s", user.id)

        except Exception as exc:
            logger.exception(
                "Failed to delete data for user_id=%s",
                user.id,
            )
            raise DatabaseError(
                "Failed to delete user financial data.",
                details={"user_id": user.id},
            ) from exc
