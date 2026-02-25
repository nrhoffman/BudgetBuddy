"""
Dependency providers for FastAPI routes.

This module defines FastAPI dependencies for database sessions, services,
and user authentication. Each provider initializes the relevant service
layer with proper repositories and handles resource cleanup.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.logger import logger
from app.auth.jwt import decode_jwt
from app.db.session import SESSIONLOCAL
from app.repositories.user_repository import UserRepository
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.bank_repository import BankRepository
from app.repositories.raw_provider_repository import RawProviderRepository
from app.models.user import User
from app.models.banking_service_deps import BankingServiceDependencies
from app.providers.plaid_sandbox import PlaidSandbox
from app.services.account_service import AccountService
from app.services.auth_service import AuthService
from app.services.banking_service import BankingService
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------------------------
# Database session dependency
# ---------------------------
def get_db() -> Session:
    """
    Yield a SQLAlchemy database session and ensure proper cleanup.

    Yields:
        Session: Active SQLAlchemy session.

    Ensures:
        The session is closed after use, even if an exception occurs.
    """
    db = SESSIONLOCAL()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------
# Service dependencies
# ---------------------------
def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    """
    Provide a fully initialized AccountService with repositories.

    Args:
        db: SQLAlchemy session dependency.

    Returns:
        AccountService: Service instance ready for use.
    """
    return AccountService(
        account_repo=AccountRepository(db),
        bank_repo=BankRepository(db),
        txn_repo=TransactionRepository(db)
    )


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Provide a fully initialized AuthService with UserRepository.

    Args:
        db: SQLAlchemy session dependency.

    Returns:
        AuthService: Service instance ready for authentication operations.
    """
    return AuthService(user_repo=UserRepository(db))


def get_banking_service(db: Session = Depends(get_db)) -> BankingService:
    """
    Provide a fully initialized BankingService with AccountService, repositories,
    and PlaidSandbox provider.

    Args:
        db: SQLAlchemy session dependency.

    Returns:
        BankingService: Service instance ready for banking operations.
    """
    account_service = AccountService(
        account_repo=AccountRepository(db),
        bank_repo=BankRepository(db),
        txn_repo=TransactionRepository(db)
    )
    bank_repo = BankRepository(db)
    raw_provider_repo = RawProviderRepository(db)
    banking_provider = PlaidSandbox()

    deps = BankingServiceDependencies(
        account_service=account_service,
        bank_repo=bank_repo,
        raw_provider_repo=raw_provider_repo,
        banking_provider=banking_provider
    )

    return BankingService(deps)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """
    Provide a fully initialized UserService with repositories.

    Args:
        db: SQLAlchemy session dependency.

    Returns:
        UserService: Service instance ready for user operations.
    """
    account_repo = AccountRepository(db)
    bank_repo = BankRepository(db)
    user_repo = UserRepository(db)
    raw_provider_repo = RawProviderRepository(db)

    return UserService(
        account_repo=account_repo,
        bank_repo=bank_repo,
        raw_provider_repo=raw_provider_repo,
        user_repo=user_repo
    )


# ---------------------------
# Authenticated user dependency
# ---------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Retrieve the currently authenticated user based on JWT token.

    Args:
        token: OAuth2 bearer token from request header.
        db: SQLAlchemy session dependency.

    Returns:
        User: Authenticated user instance.

    Raises:
        HTTPException:
            - 401 if the token is invalid or missing 'sub' claim.
            - 401 if the user does not exist in the database.
    """
    try:
        payload = decode_jwt(token)
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("JWT payload missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = UserRepository(db).get_by_id(user_id)
        if not user:
            logger.warning("Authentication failed: user_id '%s' not found", user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to decode or validate JWT: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
