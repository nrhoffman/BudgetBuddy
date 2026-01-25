"""
Authentication API endpoints: login, sign-up, and check authentication.
"""

import uuid
from fastapi import APIRouter, Depends

from app.auth.password import hash_password
from app.dependencies import get_auth_service, get_current_user
from app.models.user import User, UserCreate
from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(
    req: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate a user and return login result.

    Args:
        req: LoginRequest object containing username and password.
        budget_service: Injected BudgetService instance.

    Returns:
        Result of login operation.
    """
    return auth_service.login(username=req.username, password=req.password)


@router.post("/sign-up")
def create_user(
    user_create: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Create a new user with hashed password.

    Args:
        user_create: UserCreate object with user details.
        budget_service: Injected BudgetService instance.

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
    return auth_service.create_user(user)


@router.post("/check-login")
def check_login(_current_user=Depends(get_current_user)):
    """
    Simple endpoint to verify user authentication.

    Args:
        current_user: Injected authenticated user.

    Returns:
        Success message if authentication passes.
    """
    return {"message": "success"}
