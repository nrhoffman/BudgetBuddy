"""
Repository for managing bank item tokens and cursors in the database.

Provides methods to save, update, and retrieve bank tokens and incremental
sync cursors, with logging and exception handling for database operations.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from app.db.bank_item_token_orm import BankItemToken
from app.db.bank_item_cursor_orm import BankItemCursor
from app.logger import logger


class BankRepository:
    """
    Repository for saving and retrieving bank item tokens and cursors.

    All methods handle SQLAlchemy exceptions and ensure session rollback on failure.
    """

    def __init__(self, session: Session):
        """
        Initialize the repository with a SQLAlchemy session.

        Args:
            session (Session): SQLAlchemy session instance.
        """
        self.session = session

    # ---------------------------
    # Token methods
    # ---------------------------
    def save_token(
        self,
        user_id: str,
        provider: str,
        institution_id: str,
        institution_name: Optional[str],
        access_token: str,
        item_id: str,
    ) -> None:
        """
        Save or update a bank item token for a user.

        Args:
            user_id (str): User identifier.
            provider (str): Bank provider name.
            institution_id (str): Institution identifier.
            institution_name (Optional[str]): Institution name.
            access_token (str): Access token.
            item_id (str): Bank item ID.

        Raises:
            RuntimeError: If database commit fails.
        """
        try:
            stmt = select(BankItemToken).where(
                BankItemToken.user_id == user_id,
                BankItemToken.provider == provider,
                BankItemToken.institution_id == institution_id,
            )
            token = self.session.scalar(stmt)

            if token:
                logger.debug("Updating existing bank token for user %s, institution %s",
                             user_id, institution_id)
                token.access_token = access_token
                token.item_id = item_id
                token.institution_name = institution_name
            else:
                logger.debug("Creating new bank token for user %s, institution %s",
                             user_id, institution_id)
                token = BankItemToken(
                    user_id=user_id,
                    provider=provider,
                    institution_id=institution_id,
                    institution_name=institution_name,
                    access_token=access_token,
                    item_id=item_id,
                )
                self.session.add(token)

            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.exception(
                "Failed to save bank token for user %s, institution %s: %s",
                user_id,
                institution_id,
                exc
            )
            raise RuntimeError(
                f"Failed to save bank token for user {user_id}, "
                f"institution {institution_id}: {exc}"
            ) from exc

    def get_by_user(self, user_id: str, institution_id: str) -> Optional[BankItemToken]:
        """
        Fetch a bank item token for a given user and institution.

        Args:
            user_id (str): User identifier.
            institution_id (str): Institution identifier.

        Returns:
            Optional[BankItemToken]: Token instance if found, otherwise None.

        Raises:
            RuntimeError: If query fails.
        """
        try:
            token = (
                self.session.query(BankItemToken)
                .filter_by(user_id=user_id, institution_id=institution_id)
                .one_or_none()
            )
            logger.debug("Fetched token for user %s, institution %s: %s",
                         user_id, institution_id, token)
            return token
        except SQLAlchemyError as exc:
            logger.exception(
                "Failed to fetch bank token for user %s, institution %s: %s",
                user_id,
                institution_id,
                exc
            )
            raise RuntimeError(
                f"Failed to fetch bank token for user {user_id}, "
                f"institution {institution_id}: {exc}"
            ) from exc

    def get_token_by_item_id(self, item_id: str) -> Optional[BankItemToken]:
        """
        Fetch a bank item token by its item ID.

        Args:
            item_id (str): Bank item ID.

        Returns:
            Optional[BankItemToken]: Token instance if found, otherwise None.

        Raises:
            RuntimeError: If query fails.
        """
        try:
            token = (
                self.session.query(BankItemToken)
                .filter_by(item_id=item_id)
                .one_or_none()
            )
            logger.debug("Fetched token for item_id %s: %s", item_id, token)
            return token
        except SQLAlchemyError as exc:
            logger.exception("Failed to fetch bank token for item_id %s", item_id)
            raise RuntimeError(
                f"Failed to fetch bank token for item_id {item_id}: {exc}"
            ) from exc

    # ---------------------------
    # Cursor methods
    # ---------------------------
    def save_cursor(self, user_id: str, item_id: str, cursor: str) -> None:
        """
        Save or update a bank item's incremental sync cursor.

        Args:
            user_id (str): User identifier.
            item_id (str): Bank item ID.
            cursor (str): Cursor value.

        Raises:
            RuntimeError: If database commit fails.
        """
        try:
            existing = (
                self.session.query(BankItemCursor)
                .filter_by(user_id=user_id, item_id=item_id)
                .one_or_none()
            )
            if existing:
                logger.debug("Updating existing cursor for user %s, item %s",
                             user_id,
                             item_id
                )
                existing.cursor = cursor
                existing.updated_at = datetime.now(timezone.utc)
            else:
                logger.debug("Creating new cursor for user %s, item %s",
                             user_id,
                             item_id
                )
                new_cursor = BankItemCursor(
                    user_id=user_id,
                    item_id=item_id,
                    cursor=cursor,
                )
                self.session.add(new_cursor)

            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.exception("Failed to save cursor for user %s, item %s",
                             user_id, item_id
            )
            raise RuntimeError(
                f"Failed to save cursor for user "
                f"{user_id}, item {item_id}: {exc}"
            ) from exc

    def get_cursor_by_item_id(self, item_id: str) -> Optional[BankItemCursor]:
        """
        Fetch the incremental sync cursor for a bank item.

        Args:
            item_id (str): Bank item ID.

        Returns:
            Optional[BankItemCursor]: Cursor instance if found, otherwise None.

        Raises:
            RuntimeError: If query fails.
        """
        try:
            cursor = (
                self.session.query(BankItemCursor)
                .filter_by(item_id=item_id)
                .one_or_none()
            )
            logger.debug("Fetched cursor for item_id %s: %s", item_id, cursor)
            return cursor
        except SQLAlchemyError as exc:
            logger.exception("Failed to fetch cursor for item_id %s", item_id)
            raise RuntimeError(f"Failed to fetch cursor for item_id {item_id}") from exc
