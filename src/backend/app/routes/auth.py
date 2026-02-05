"""
Authentication API endpoints: login, sign-up, and check authentication.

Provides structured endpoints for user login, account creation, and
authentication verification, with type hints, logging, and exception handling.
"""

import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from app.auth.password import hash_password
from app.dependencies import get_auth_service, get_current_user
from app.models.user import User, UserCreate
from app.models.auth import LoginRequest
from app.services.auth_service import AuthService
from app.logger import logger

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(
    req: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    Authenticate a user and return login result.

    Args:
        req: LoginRequest object containing username and password.
        auth_service: Injected AuthService instance.

    Returns:
        Result of login operation.

    Raises:
        HTTPException: If login fails.
    """
    try:
        result = auth_service.login(username=req.username, password=req.password)
        logger.debug("User %s successfully logged in", req.username)
        return result
    except Exception as exc:
        logger.exception("Failed login attempt for user %s", req.username)
        raise HTTPException(status_code=401, detail="Invalid credentials") from exc


@router.post("/sign-up")
def create_user(
    user_create: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Create a new user with hashed password.

    Args:
        user_create: UserCreate object with user details.
        auth_service: Injected AuthService instance.

    Returns:
        The created User object.

    Raises:
        HTTPException: If user creation fails.
    """
    try:
        user = User(
            id=str(uuid.uuid4()),
            username=user_create.username,
            email=user_create.email,
            hashed_password=hash_password(user_create.password),
            role=user_create.role,
        )
        created_user = auth_service.create_user(user)
        logger.debug("Created new user %s with id %s", user.username, user.id)
        return created_user
    except Exception as exc:
        logger.exception("Failed to create user %s", user_create.username)
        raise HTTPException(status_code=500, detail="Failed to create user") from exc


@router.post("/check-login")
def check_login(_current_user: User = Depends(get_current_user)) -> Dict[str, str]:
    """
    Simple endpoint to verify user authentication.

    Args:
        _current_user: Injected authenticated user.

    Returns:
        Success message if authentication passes.

    Raises:
        HTTPException: If user is not authenticated.
    """
    if not _current_user:
        logger.warning("Unauthorized access attempt to check-login")
        raise HTTPException(status_code=401, detail="Not authenticated")

    logger.debug("Authentication check passed for user %s", _current_user.username)
    return {"message": "success"}
