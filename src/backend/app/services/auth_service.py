"""
Authentication service for user registration and login.

Provides functionality for creating users, validating credentials,
and issuing JWT access tokens. Includes structured logging and
consistent error handling.
"""

from typing import Dict
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.logger import logger
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    """
    Service responsible for user authentication and authorization logic.
    """

    def __init__(self, user_repo: UserRepository):
        """
        Initialize the authentication service.

        Args:
            user_repo: Repository used for user persistence and lookup.
        """
        self.user_repo = user_repo

    # ---------------------------
    # User creation
    # ---------------------------
    def create_user(self, user: User) -> Dict[str, str]:
        """
        Persist a new user record.

        Args:
            user: User model instance to be created.

        Returns:
            Dict containing success message and created user ID.

        Raises:
            HTTPException: If user creation fails due to validation,
                           uniqueness constraints, or database errors.
        """
        try:
            self.user_repo.add(user)
            logger.info("User created: id=%s, username=%s", user.id, user.username)
            return {"message": "User created successfully", "user_id": user.id}

        except IntegrityError as exc:
            error_msg = str(exc.orig)

            if "users_email_key" in error_msg:
                logger.warning("Email conflict for user creation: %s", user.email)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists",
                ) from exc

            if "users_username_key" in error_msg:
                logger.warning("Username conflict for user creation: %s", user.username)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists",
                ) from exc

            logger.warning("Integrity error creating user: %s", user.username)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user data",
            ) from exc

        except SQLAlchemyError as exc:
            logger.error("Database error creating user %s: %s",
                         user.username,
                         exc,
                         exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            ) from exc

    # ---------------------------
    # User login
    # ---------------------------
    def login(self, username: str, password: str) -> Dict[str, str]:
        """
        Authenticate a user and issue a JWT access token.

        Args:
            username: Username provided by the client.
            password: Plain-text password provided by the client.

        Returns:
            Dict containing access token, token type, and success message.

        Raises:
            HTTPException: If authentication fails due to invalid credentials.
        """
        logger.info("Login attempt for username=%s", username)

        try:
            user = self.user_repo.get_by_username(username)
        except Exception as exc:
            logger.error("Failed to fetch user %s for login: %s",
                         username,
                         exc,
                         exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to authenticate user",
            ) from exc

        if not user or not verify_password(password, user.hashed_password):
            logger.warning("Invalid login attempt for username=%s", username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        token = create_access_token(subject=user.id)
        logger.info("User %s logged in successfully", user.id)

        return {"message": "Login successful",
                "access_token": token,
                "token_type": "bearer"
        }
