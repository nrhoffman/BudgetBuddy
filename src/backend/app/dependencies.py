"""
Dependency providers for FastAPI routes, including DB session, services, and auth.
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
from app.services.account_service import AccountService
from app.services.auth_service import AuthService
from app.services.banking_service import BankingService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db() -> Session:
    """
    Yield a SQLAlchemy database session and ensure it is closed after use.

    Yields:
        Session: A SQLAlchemy database session.
    """
    db = SESSIONLOCAL()
    try:
        yield db
    finally:
        db.close()


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    """
    Provide a fully initialized AccountService with its repository.

    Args:
        db: SQLAlchemy session dependency.

    Returns:
        AccountService: Initialized service.
    """
    return AccountService(account_repo=AccountRepository(db))


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Provide a fully initialized AuthService with its repository.

    Args:
        db: SQLAlchemy session dependency.

    Returns:
        AuthService: Initialized service.
    """
    return AuthService(user_repo=UserRepository(db))


def get_banking_service(db: Session = Depends(get_db)) -> BankingService:
    """
    Provide a fully initialized BankingService with AccountService and
    PlaidSandbox provider.

    Args:
        db: SQLAlchemy session dependency.

    Returns:
        BankingService: Initialized service with provider.
    """
    account_service = AccountService(account_repo=AccountRepository(db))
    banking_provider = PlaidSandbox()
    return BankingService(
        account_service=account_service, banking_provider=banking_provider
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Retrieve the currently authenticated user based on JWT token.

    Args:
        token: OAuth2 bearer token from request header.
        db: SQLAlchemy session dependency.

    Raises:
        HTTPException: If token is invalid or user not found.

    Returns:
        User: Authenticated user instance.
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
