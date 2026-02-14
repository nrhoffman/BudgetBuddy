"""
Repository layer for persisting raw provider events to the database.

This module defines the RawProviderRepository, which provides methods
to store raw event data returned by external banking providers. Events
are persisted in the `RawProviderORM` table and include payload, identity,
cursor information, and timestamps.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.raw_provider_orm import RawProviderORM
from app.models.raw_provider_data import RawProviderData


class RawProviderRepository:
    """
    Repository for storing raw provider events in the database.

    Provides a method to save RawProviderData objects by mapping them
    to the SQLAlchemy ORM model.

    Attributes:
        session (Session): SQLAlchemy session used for database operations.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a SQLAlchemy session.

        Args:
            session (Session): Active SQLAlchemy session.
        """

        self.session = session

    def save(self, event: RawProviderData) -> None:
        """
        Persist a RawProviderData object to the database.

        Maps the domain-level RawProviderData to the RawProviderORM model
        and adds it to the session. Caller is responsible for committing
        the session.

        Args:
            event (RawProviderData): The raw provider event to save.

        Notes:
            - Identity and cursor information are optional.
            - The fetched_at timestamp will be taken from event.occurred_at
              if provided.
        """

        orm = RawProviderORM(
            provider=event.provider,
            endpoint=event.endpoint,
            user_id=event.identity.user_id if event.identity else None,
            item_id=event.identity.item_id if event.identity else None,
            cursor_before=event.cursor.before if event.cursor else None,
            cursor_after=event.cursor.after if event.cursor else None,
            payload=self.json_safe(event.payload),
            fetched_at=event.occurred_at,
        )
        self.session.add(orm)

    def delete_all(self, user_id: str) -> None:
        """
        Delete all raw provider records associated with a user.

        Executes a bulk delete operation on the RawProviderORM table
        for the specified user identifier. The caller is responsible
        for committing the session.

        Args:
            user_id (str): Identifier of the user whose raw provider
                records should be removed.

        Notes:
            - This operation performs a bulk delete and does not load
              ORM objects into memory.
            - The SQLAlchemy session is not committed within this method.
        """
        (
            self.session.query(RawProviderORM)
            .filter(RawProviderORM.user_id == user_id)
            .delete(synchronize_session=False)
        )

    def json_safe(self, value):
        """
        Recursively convert Python objects into JSON-serializable formats.

        Args:
            value: Any Python object, potentially including nested dicts, lists,
                datetime, date, or Decimal types.

        Returns:
            A JSON-serializable version of `value` where:
                - `dict` objects are converted recursively.
                - `list` objects are converted recursively.
                - `datetime` and `date` objects are converted to ISO 8601 strings.
                - `Decimal` objects are converted to floats.
                - All other types are returned unchanged.

        Notes:
            This method is useful for preparing complex nested data structures
            (including ORM objects, payloads, or API responses) for JSON serialization.
        """

        if isinstance(value, dict):
            return {k: self.json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.json_safe(v) for v in value]
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return value
