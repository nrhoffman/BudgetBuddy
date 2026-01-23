"""
Repository for managing users in the database.
"""

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.user_orm import UserORM
from app.mappers.user_mapper import orm_to_domain_user
from app.models.user import User


class UserRepository:
    """
    Repository for CRUD operations on users.
    """

    def __init__(self, session: Session):
        """
        Initialize repository with a SQLAlchemy session.

        Args:
            session: SQLAlchemy Session instance.
        """
        self.session = session

    def get_by_id(self, user_id: str) -> User:
        """
        Fetch a user by ID.

        Args:
            user_id: The user's ID.

        Returns:
            User instance.

        Raises:
            ValueError: If the user does not exist.
            RuntimeError: If the query fails.
        """
        try:
            orm = (
                self.session.query(UserORM)
                .filter(UserORM.id == user_id)
                .first()
            )
            if not orm:
                raise ValueError(f"User {user_id} not found")
            return orm_to_domain_user(orm)
        except SQLAlchemyError as exc:
            raise RuntimeError(f"Failed to fetch user {user_id}") from exc

    def get_by_username(self, username: str) -> User:
        """
        Fetch a user by username.

        Args:
            username: The username to search for.

        Returns:
            User instance.

        Raises:
            ValueError: If the user does not exist.
            RuntimeError: If the query fails.
        """
        try:
            orm = (
                self.session.query(UserORM)
                .filter(UserORM.username == username)
                .first()
            )
            if not orm:
                raise ValueError(f"User {username} not found")
            return orm_to_domain_user(orm)
        except SQLAlchemyError as exc:
            raise RuntimeError(f"Failed to fetch user {username}") from exc

    def add(self, user: User) -> None:
        """
        Add a new user to the database.

        Args:
            user: User domain object to add.

        Raises:
            ValueError: If a unique constraint is violated.
            RuntimeError: If the insert fails.
        """
        try:
            orm = UserORM(
                id=user.id,
                username=user.username,
                email=user.email,
                hashed_password=user.hashed_password,
                role=user.role,
            )
            self.session.add(orm)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ValueError(
                f"Integrity error creating user {user.username}"
            ) from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise RuntimeError(
                f"Failed to add user {user.username}"
            ) from exc
