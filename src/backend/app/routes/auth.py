"""
Authentication API endpoints: login, sign-up, and check authentication.

Provides structured endpoints for user login, account creation, and
authentication verification
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from app.auth.password import hash_password
from app.dependencies import get_auth_service, get_current_user
from app.models.user import User, UserCreate
from app.models.auth import LoginRequest
from app.services.auth_service import AuthService
from app.logger import logger
from app.exceptions import AuthenticationError

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
    """
    token = auth_service.login(username=req.username, password=req.password)
    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/sign-up")
def create_user(
    user_create: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """
    Create a new user with hashed password.

    Args:
        user_create: UserCreate object with user details.
        auth_service: Injected AuthService instance.

    Returns:
        The created User object.
    """
    user = User(
        id=str(uuid.uuid4()),
        username=user_create.username,
        email=user_create.email,
        hashed_password=hash_password(user_create.password),
        role=user_create.role,
    )
    created_user = auth_service.create_user(user)
    return {"message": "User created successfully", "user_id": created_user}


@router.post("/check-login")
def check_login(_current_user: User = Depends(get_current_user)) -> dict[str, str]:
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
        raise AuthenticationError("Not authenticated")

    logger.info("Authentication check passed for user %s", _current_user.username)
    return {"message": "success"}
