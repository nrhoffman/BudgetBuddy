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

# ---------------------------
# Test get_db
# ---------------------------
def test_get_db_yields_and_closes():
    class DummySession:
        closed = False
        def close(self):
            self.closed = True

    with patch("app.dependencies.SESSIONLOCAL", return_value=DummySession()) as mock_session:
        gen = get_db()
        session = next(gen)
        assert session.closed is False
        try:
            next(gen)
        except StopIteration:
            pass
        assert session.closed is True

# ---------------------------
# Test get_account_service
# ---------------------------
def test_get_account_service_returns_instance():
    mock_db = MagicMock(spec=Session)
    service = get_account_service(db=mock_db)
    from app.services.account_service import AccountService
    assert isinstance(service, AccountService)

# ---------------------------
# Test get_auth_service
# ---------------------------
def test_get_auth_service_returns_instance():
    mock_db = MagicMock(spec=Session)
    service = get_auth_service(db=mock_db)
    from app.services.auth_service import AuthService
    assert isinstance(service, AuthService)

# ---------------------------
# Test get_banking_service
# ---------------------------
def test_get_banking_service_returns_instance():
    mock_db = MagicMock(spec=Session)
    service = get_banking_service(db=mock_db)
    from app.services.banking_service import BankingService
    assert isinstance(service, BankingService)
    # Check that it has an account_service and bank_repo
    assert hasattr(service, "account_service")
    assert hasattr(service, "bank_repo")
    assert hasattr(service, "banking_provider")

# ---------------------------
# Test get_current_user
# ---------------------------
@pytest.fixture
def mock_user():
    user = User(id="user123", username="tester", email="test@example.com", hashed_password="hashed", role="user")
    return user

def test_get_current_user_success(mock_user):
    token = "dummy"
    db_mock = MagicMock()
    db_mock_user_repo = MagicMock(spec=UserRepository)
    db_mock_user_repo.get_by_id.return_value = mock_user

    with patch("app.dependencies.decode_jwt", return_value={"sub": mock_user.id}), \
         patch("app.dependencies.UserRepository", return_value=db_mock_user_repo):
        user = get_current_user(token=token, db=db_mock)
        assert user.id == mock_user.id
        assert user.username == mock_user.username

def test_get_current_user_missing_sub(mock_user):
    token = "dummy"
    db_mock = MagicMock()
    with patch("app.dependencies.decode_jwt", return_value={}):
        with pytest.raises(HTTPException) as excinfo:
            get_current_user(token=token, db=db_mock)
        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_current_user_user_not_found(mock_user):
    token = "dummy"
    db_mock = MagicMock()
    db_mock_user_repo = MagicMock(spec=UserRepository)
    db_mock_user_repo.get_by_id.return_value = None

    with patch("app.dependencies.decode_jwt", return_value={"sub": mock_user.id}), \
         patch("app.dependencies.UserRepository", return_value=db_mock_user_repo):
        with pytest.raises(HTTPException) as excinfo:
            get_current_user(token=token, db=db_mock)
        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_current_user_decode_error(mock_user):
    token = "dummy"
    db_mock = MagicMock()
    with patch("app.dependencies.decode_jwt", side_effect=Exception("bad token")):
        with pytest.raises(HTTPException) as excinfo:
            get_current_user(token=token, db=db_mock)
        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
