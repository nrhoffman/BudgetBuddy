"""
Repository for managing bank item tokens and cursors in the database.

Provides methods to save, update, and retrieve bank tokens and incremental
sync cursors
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.bank_item_token_orm import BankItemTokenORM
from app.db.bank_item_cursor_orm import BankItemCursorORM
from app.models.exchange_token import ExchangeToken


class BankRepository:
    """
    Repository for saving and retrieving bank item tokens and cursors.
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
        item_id: str,
        exchange_token: ExchangeToken,
    ) -> None:
        """
        Save or update a bank item token for a user.

        Args:
            user_id (str): User identifier.
            provider (str): Bank provider name.
            item_id (str): Bank item ID.
            exchange_token (ExchangeToken): Exchange token object.
        """
        stmt = select(BankItemTokenORM).where(
            BankItemTokenORM.user_id == user_id,
            BankItemTokenORM.provider == provider,
            BankItemTokenORM.institution_id == exchange_token.institution_id,
        )
        token = self.session.scalar(stmt)

        if token:
            token.access_token = exchange_token.public_token
            token.item_id = item_id
            token.institution_name = exchange_token.institution_name
        else:
            token = BankItemTokenORM(
                user_id=user_id,
                provider=provider,
                institution_id=exchange_token.institution_id,
                institution_name=exchange_token.institution_name,
                access_token=exchange_token.public_token,
                item_id=item_id,
            )
            self.session.add(token)

    def get_by_user(
            self,
            user_id: str,
            institution_id: str
    ) -> Optional[BankItemTokenORM]:
        """
        Fetch a bank item token for a given user and institution.

        Args:
            user_id (str): User identifier.
            institution_id (str): Institution identifier.

        Returns:
            Optional[BankItemTokenORM]: Token instance if found, otherwise None.
        """
        token = (
            self.session.query(BankItemTokenORM)
            .filter_by(user_id=user_id, institution_id=institution_id)
            .one_or_none()
        )
        return token

    def get_token_by_item_id(self, item_id: str) -> Optional[BankItemTokenORM]:
        """
        Fetch a bank item token by its item ID.

        Args:
            item_id (str): Bank item ID.

        Returns:
            Optional[BankItemTokenORM]: Token instance if found, otherwise None.

        Raises:
            RuntimeError: If query fails.
        """
        token = (
            self.session.query(BankItemTokenORM)
            .filter_by(item_id=item_id)
            .one_or_none()
        )
        return token

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
        """
        existing = (
            self.session.query(BankItemCursorORM)
            .filter_by(user_id=user_id, item_id=item_id)
            .one_or_none()
        )
        if existing:
            existing.cursor = cursor
            existing.updated_at = datetime.now(timezone.utc)
        else:
            new_cursor = BankItemCursorORM(
                user_id=user_id,
                item_id=item_id,
                cursor=cursor,
            )
            self.session.add(new_cursor)

    def get_cursor_by_item_id(self, item_id: str) -> Optional[BankItemCursorORM]:
        """
        Fetch the incremental sync cursor for a bank item.

        Args:
            item_id (str): Bank item ID.

        Returns:
            Optional[BankItemCursorORM]: Cursor instance if found, otherwise None.
        """
        cursor = (
            self.session.query(BankItemCursorORM)
            .filter_by(item_id=item_id)
            .one_or_none()
        )
        return cursor

    # ---------------------------
    # Institution methods
    # --------------------------
    def get_institutions(self, user_id: str) -> list[dict]:
        """
        Retrieve a list of financial institutions for a user.

        Args:
            user_id (str): User identifier.

        Returns:
            list[dict]: List of institutions with id and name.
        """
        institutions = self.session.execute(
            select(
                BankItemTokenORM.institution_id,
                BankItemTokenORM.institution_name,
            )
            .where(BankItemTokenORM.user_id == user_id)
            .group_by(
                BankItemTokenORM.institution_id,
                BankItemTokenORM.institution_name
            )
        ).all()

        return [
            {
                "institution_id": inst.institution_id,
                "institution_name": inst.institution_name,
            }
            for inst in institutions
        ]
