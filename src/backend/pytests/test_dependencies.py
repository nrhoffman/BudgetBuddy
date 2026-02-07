"""
Unit tests for FastAPI dependency providers.

Validates that:
- Database sessions are yielded and properly closed.
- Service dependencies return correctly initialized service instances.
- JWT authentication dependency returns a valid User or raises appropriate exceptions.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import (
    get_db,
    get_account_service,
    get_auth_service,
    get_banking_service,
    get_current_user,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.account_service import AccountService
from app.services.auth_service import AuthService
from app.services.banking_service import BankingService


# ---------------------------
# Test get_db
# ---------------------------
def test_get_db_yields_and_closes():
    """Ensure get_db yields a session and closes it after use."""
    class DummySession:
        closed = False
        def commit(self): pass
        def rollback(self): pass
        def close(self): self.closed = True

    with patch("app.dependencies.SESSIONLOCAL", return_value=DummySession()):
        gen = get_db()
        session = next(gen)
        assert session.closed is False

        # Complete generator to trigger cleanup
        with pytest.raises(StopIteration):
            next(gen)

        assert session.closed is True


# ---------------------------
# Test service providers
# ---------------------------
def test_get_account_service_returns_instance():
    """Ensure get_account_service returns an AccountService instance."""
    mock_db = MagicMock(spec=Session)
    service = get_account_service(db=mock_db)
    assert isinstance(service, AccountService)


def test_get_auth_service_returns_instance():
    """Ensure get_auth_service returns an AuthService instance."""
    mock_db = MagicMock(spec=Session)
    service = get_auth_service(db=mock_db)
    assert isinstance(service, AuthService)


def test_get_banking_service_returns_instance():
    """Ensure get_banking_service returns a BankingService instance with correct attributes."""
    mock_db = MagicMock(spec=Session)
    service = get_banking_service(db=mock_db)
    assert isinstance(service, BankingService)
    assert hasattr(service, "account_service")
    assert hasattr(service, "bank_repo")
    assert hasattr(service, "banking_provider")


# ---------------------------
# Test get_current_user
# ---------------------------
@pytest.fixture
def mock_user():
    """Provide a dummy User instance for authentication tests."""
    return User(
        id="user123",
        username="tester",
        email="test@example.com",
        hashed_password="hashed",
        role="user"
    )


def test_get_current_user_success(mock_user):
    """Ensure get_current_user returns the user when JWT is valid."""
    token = "dummy"
    db_mock = MagicMock()
    user_repo_mock = MagicMock(spec=UserRepository)
    user_repo_mock.get_by_id.return_value = mock_user

    with patch("app.dependencies.decode_jwt", return_value={"sub": mock_user.id}), \
         patch("app.dependencies.UserRepository", return_value=user_repo_mock):
        user = get_current_user(token=token, db=db_mock)
        assert user.id == mock_user.id
        assert user.username == mock_user.username


def test_get_current_user_missing_sub(mock_user):
    """Ensure get_current_user raises HTTP 401 if JWT payload is missing 'sub'."""
    token = "dummy"
    db_mock = MagicMock()

    with patch("app.dependencies.decode_jwt", return_value={}):
        with pytest.raises(HTTPException) as excinfo:
            get_current_user(token=token, db=db_mock)
        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_user_not_found(mock_user):
    """Ensure get_current_user raises HTTP 401 if user ID from JWT does not exist in DB."""
    token = "dummy"
    db_mock = MagicMock()
    user_repo_mock = MagicMock(spec=UserRepository)
    user_repo_mock.get_by_id.return_value = None

    with patch("app.dependencies.decode_jwt", return_value={"sub": mock_user.id}), \
         patch("app.dependencies.UserRepository", return_value=user_repo_mock):
        with pytest.raises(HTTPException) as excinfo:
            get_current_user(token=token, db=db_mock)
        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_decode_error(mock_user):
    """Ensure get_current_user raises HTTP 401 if JWT decoding fails."""
    token = "dummy"
    db_mock = MagicMock()

    with patch("app.dependencies.decode_jwt", side_effect=Exception("invalid token")):
        with pytest.raises(HTTPException) as excinfo:
            get_current_user(token=token, db=db_mock)
        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
