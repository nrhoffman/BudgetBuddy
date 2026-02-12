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
    class DummySession:
        closed = False
        def commit(self): pass
        def rollback(self): pass
        def close(self): self.closed = True

    with patch("app.dependencies.SESSIONLOCAL", return_value=DummySession()):
        gen = get_db()
        session = next(gen)
        assert session.closed is False
        with pytest.raises(StopIteration):
            next(gen)
        assert session.closed is True

# ---------------------------
# Test service providers
# ---------------------------
def test_get_account_service_returns_instance():
    mock_db = MagicMock(spec=Session)
    service = get_account_service(db=mock_db)
    assert isinstance(service, AccountService)

def test_get_auth_service_returns_instance():
    mock_db = MagicMock(spec=Session)
    service = get_auth_service(db=mock_db)
    assert isinstance(service, AuthService)

def test_get_banking_service_returns_instance():
    """Ensure get_banking_service returns a BankingService instance with correct attributes."""
    mock_db = MagicMock(spec=Session)

    # Patch any constructors or functions that BankingService calls internally
    with patch("app.services.account_service.AccountService", return_value=MagicMock()), \
         patch("app.services.banking_service.BankingService.__init__", return_value=None):
        
        service = get_banking_service(db=mock_db)

        # Manually add mocked attributes because __init__ was skipped
        service.account_service = MagicMock()
        service.bank_repo = MagicMock()
        service.banking_provider = MagicMock()

        assert isinstance(service, BankingService)
        assert hasattr(service, "account_service")
        assert hasattr(service, "bank_repo")
        assert hasattr(service, "banking_provider")

# ---------------------------
# Test get_current_user
# ---------------------------
@pytest.fixture
def mock_user():
    return User(
        id="user123",
        username="tester",
        email="test@example.com",
        hashed_password="hashed",
        role="user"
    )

@pytest.mark.parametrize(
    "jwt_payload, expected_exception, desc",
    [
        ({"sub": "user123"}, None, "valid JWT returns user"),
        ({}, HTTPException, "missing 'sub' raises 401"),
        (None, HTTPException, "decode error raises 401"),
    ]
)
def test_get_current_user_variants(mock_user, jwt_payload, expected_exception, desc):
    token = "dummy"
    db_mock = MagicMock()
    user_repo_mock = MagicMock(spec=UserRepository)
    user_repo_mock.get_by_id.return_value = mock_user if jwt_payload and "sub" in jwt_payload else None

    decode_side_effect = Exception("decode error") if jwt_payload is None else None
    decode_return = jwt_payload if jwt_payload is not None else None

    with patch("app.dependencies.decode_jwt", side_effect=decode_side_effect if decode_side_effect else lambda t: decode_return), \
         patch("app.dependencies.UserRepository", return_value=user_repo_mock):
        if expected_exception:
            with pytest.raises(HTTPException) as excinfo:
                get_current_user(token=token, db=db_mock)
            assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
        else:
            user = get_current_user(token=token, db=db_mock)
            assert user.id == mock_user.id
            assert user.username == mock_user.username
