"""
Repository for managing bank item tokens in the database.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.bank_item_token import BankItemToken


class BankTokenRepository:
    """
    Repository for saving and retrieving bank item tokens.
    """

    def __init__(self, session: Session):
        """
        Initialize repository with a SQLAlchemy session.

        Args:
            session: SQLAlchemy Session instance.
        """
        self.session = session

    def save(
        self, user_id: str, provider: str, access_token: str, item_id: str
    ) -> None:
        """
        Save a bank item token to the database.

        Args:
            user_id: ID of the user.
            provider: Banking provider name.
            access_token: Access token from the provider.
            item_id: Bank item ID.

        Raises:
            RuntimeError: If saving to the database fails.
        """
        try:
            token = BankItemToken(
                user_id=user_id,
                provider=provider,
                access_token=access_token,
                item_id=item_id,
            )
            self.session.add(token)
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise RuntimeError(
                f"Failed to save bank token for user {user_id}, provider {provider}"
            ) from exc

    def get_by_user(self, user_id: str, provider: str) -> BankItemToken | None:
        """
        Fetch a bank item token for a given user and provider.

        Args:
            user_id: ID of the user.
            provider: Banking provider name.

        Returns:
            BankItemToken instance if found, otherwise None.

        Raises:
            RuntimeError: If the query fails.
        """
        try:
            return (
                self.session.query(BankItemToken)
                .filter_by(user_id=user_id, provider=provider)
                .one_or_none()
            )
        except SQLAlchemyError as exc:
            raise RuntimeError(
                f"Failed to fetch bank token for user {user_id}, provider {provider}"
            ) from exc
