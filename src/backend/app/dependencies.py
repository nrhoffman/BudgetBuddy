"""
Dependency providers for FastAPI routes, including DB session, BudgetService,
and authenticated user retrieval.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.logger import logger
from app.auth.jwt import decode_jwt
from app.db.session import SESSIONLOCAL
from app.repositories.user_repository import UserRepository
from app.repositories.account_repository import AccountRepository
from app.models.user import User
from app.providers.plaid_sandbox import PlaidSandbox
from app.services.budget_service import BudgetService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db() -> Session:
    """
    Provide a SQLAlchemy database session and ensure it is closed after use.

    Yields:
        Session: A SQLAlchemy DB session.
    """
    db = SESSIONLOCAL()
    try:
        yield db
    finally:
        db.close()


def get_budget_service(db: Session = Depends(get_db)) -> BudgetService:
    """
    Provide a fully initialized BudgetService instance with repositories
    and banking provider.

    Args:
        db: SQLAlchemy session dependency.

    Returns:
        BudgetService instance.
    """
    return BudgetService(
        session=db,
        user_repo=UserRepository(db),
        account_repo=AccountRepository(db),
        banking_provider=PlaidSandbox(),
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and return the currently authenticated user based on JWT.

    Args:
        token: OAuth2 bearer token from the request header.
        db: SQLAlchemy session dependency.

    Raises:
        HTTPException: If token is invalid or user is not found.

    Returns:
        User: Authenticated user model instance.
    """
    payload = decode_jwt(token)
    user_id = payload.get("sub")

    if not user_id:
        logger.warning("JWT payload missing 'sub' field")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        logger.warning("Authentication failed: user_id '%s' not found", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
