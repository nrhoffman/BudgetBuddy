"""
Authentication service for user registration and login.

This module defines the AuthService class, which encapsulates
authentication and authorization logic including user creation,
credential validation, and JWT access token issuance.
"""

import re

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.auth.jwt import create_access_token
from app.auth.password import verify_password, hash_password
from app.logger import logger
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.exceptions import (
    ConflictError,
    ValidationError,
    DatabaseError,
    AuthenticationError,
)


PASSWORD_REGEX = re.compile(
    r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$"
)


class AuthService:
    """
    Service responsible for authentication and authorization workflows.

    This service coordinates user persistence, credential verification,
    and token generation while enforcing domain-specific error handling
    and structured logging.
    """

    def __init__(self, user_repo: UserRepository):
        """
        Initialize the authentication service.

        Args:
            user_repo (UserRepository): Repository used to persist and
                retrieve user records.
        """
        self.user_repo = user_repo

    # ---------------------------
    # User creation
    # ---------------------------
    def create_user(self, user: User) -> str:
        """
        Create and persist a new user.

        Validates uniqueness constraints (email and username) and
        translates lower-level persistence errors into domain-specific
        exceptions.

        Args:
            user (User): User model instance to persist.

        Returns:
            str: The unique identifier of the newly created user.

        Raises:
            ConflictError: If the email or username already exists.
            ValidationError: If the user data violates validation or
                integrity constraints.
            DatabaseError: If an unexpected database error occurs.
        """

        if not PASSWORD_REGEX.match(user.password):
            raise ValidationError(
                "Password must be at least 8 characters long, "
                "include one uppercase letter, one number, "
                "and one special character."
            )

        try:
            user.hashed_password = hash_password(user.password)
            user.password = None
            self.user_repo.add(user)
            logger.info("User created: id=%s, username=%s", user.id, user.username)
            return user.id

        except IntegrityError as exc:
            error_msg = str(exc.orig)

            if "users_email_key" in error_msg:
                logger.warning("Email conflict for user creation: %s", user.email)
                raise ConflictError("Email already exists") from exc

            if "users_username_key" in error_msg:
                logger.warning("Username conflict for user creation: %s", user.username)
                raise ConflictError("Username already exists") from exc

            logger.warning("Integrity error creating user: %s", user.username)
            raise ValidationError("Invalid user data") from exc

        except SQLAlchemyError as exc:
            logger.error(
                "Database error creating user %s: %s",
                user.username,
                exc,
                exc_info=True
            )
            raise DatabaseError("Failed to create user") from exc

    # ---------------------------
    # User login
    # ---------------------------
    def login(self, username: str, password: str) -> str:
        """
        Authenticate a user and generate a JWT access token.

        Validates provided credentials against stored user data and
        issues a signed JWT on successful authentication.

        Args:
            username (str): Username provided by the client.
            password (str): Plain-text password provided by the client.

        Returns:
            str: A signed JWT access token for the authenticated user.

        Raises:
            AuthenticationError: If the credentials are invalid.
            DatabaseError: If retrieving the user from the database fails.
        """
        logger.info("Login attempt for username=%s", username)

        try:
            user = self.user_repo.get_by_username(username)
        except SQLAlchemyError as exc:
            logger.error(
                "Database error fetching user %s for login: %s",
                username,
                exc,
                exc_info=True
            )
            raise DatabaseError("Failed to authenticate user") from exc

        if not user or not verify_password(password, user.hashed_password):
            logger.warning("Invalid login attempt for username=%s", username)
            raise AuthenticationError("Invalid credentials")

        token = create_access_token(subject=user.id)
        logger.info("User %s logged in successfully", user.id)

        return token

    def verify_password(self, user: User, password: str) -> None:
        """
        Verify a user's password against the stored hashed credential.

        Args:
            user (User): Authenticated user model containing the hashed password.
            password (str): Plaintext password provided for verification.

        Raises:
            AuthenticationError: If the user does not exist or the password
                does not match the stored hash.
        """
        if not user or not verify_password(password, user.hashed_password):
            logger.warning(
                "Invalid credentials for username=%s",
                user.username if user else "unknown",
            )
            raise AuthenticationError("Invalid credentials")
