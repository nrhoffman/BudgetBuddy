import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.services.auth_service import AuthService
from app.models.user import User

# -------------------------------
# Sample user
# -------------------------------
SAMPLE_USER = User(
    id="user_1",
    username="testuser",
    email="test@example.com",
    hashed_password="hashedpassword123"
)

# -------------------------------
# Fixtures
# -------------------------------
@pytest.fixture
def mock_user_repo():
    return MagicMock()

@pytest.fixture
def auth_service(mock_user_repo):
    return AuthService(user_repo=mock_user_repo)

# -------------------------------
# Tests for create_user
# -------------------------------
def test_create_user_success(auth_service, mock_user_repo):
    mock_user_repo.add.return_value = None

    result = auth_service.create_user(SAMPLE_USER)
    assert result["message"] == "User created successfully"
    assert result["user_id"] == SAMPLE_USER.id
    mock_user_repo.add.assert_called_once_with(SAMPLE_USER)

def test_create_user_email_conflict(auth_service, mock_user_repo):
    exc = IntegrityError(
        statement=None,
        params=None,
        orig=Exception('duplicate key value violates unique constraint "users_email_key"')
    )
    mock_user_repo.add.side_effect = exc

    with pytest.raises(HTTPException) as e:
        auth_service.create_user(SAMPLE_USER)
    assert e.value.status_code == 409
    assert "Email already exists" in e.value.detail

def test_create_user_username_conflict(auth_service, mock_user_repo):
    exc = IntegrityError(
        statement=None,
        params=None,
        orig=Exception('duplicate key value violates unique constraint "users_username_key"')
    )
    mock_user_repo.add.side_effect = exc

    with pytest.raises(HTTPException) as e:
        auth_service.create_user(SAMPLE_USER)
    assert e.value.status_code == 409
    assert "Username already exists" in e.value.detail

def test_create_user_generic_integrity_error(auth_service, mock_user_repo):
    exc = IntegrityError(
        statement=None,
        params=None,
        orig=Exception("other integrity error")
    )
    mock_user_repo.add.side_effect = exc

    with pytest.raises(HTTPException) as e:
        auth_service.create_user(SAMPLE_USER)
    assert e.value.status_code == 400
    assert "Invalid user data" in e.value.detail

def test_create_user_sqlalchemy_error(auth_service, mock_user_repo):
    mock_user_repo.add.side_effect = SQLAlchemyError("DB error")

    with pytest.raises(HTTPException) as e:
        auth_service.create_user(SAMPLE_USER)
    assert e.value.status_code == 500
    assert "Failed to create user" in e.value.detail

# -------------------------------
# Tests for login
# -------------------------------
@patch("app.services.auth_service.verify_password")
@patch("app.services.auth_service.create_access_token")
def test_login_success(mock_create_token, mock_verify_password, auth_service, mock_user_repo):
    mock_user_repo.get_by_username.return_value = SAMPLE_USER
    mock_verify_password.return_value = True
    mock_create_token.return_value = "mocktoken"

    result = auth_service.login("testuser", "password123")
    assert result["message"] == "Login successful"
    assert result["access_token"] == "mocktoken"
    assert result["token_type"] == "bearer"

    mock_user_repo.get_by_username.assert_called_once_with("testuser")
    mock_verify_password.assert_called_once_with("password123", SAMPLE_USER.hashed_password)
    mock_create_token.assert_called_once_with(subject=SAMPLE_USER.id)

@patch("app.services.auth_service.verify_password")
def test_login_invalid_username(mock_verify_password, auth_service, mock_user_repo):
    mock_user_repo.get_by_username.return_value = None

    with pytest.raises(HTTPException) as e:
        auth_service.login("wronguser", "password123")
    assert e.value.status_code == 401
    assert "Invalid credentials" in e.value.detail
    mock_verify_password.assert_not_called()

@patch("app.services.auth_service.verify_password")
def test_login_invalid_password(mock_verify_password, auth_service, mock_user_repo):
    mock_user_repo.get_by_username.return_value = SAMPLE_USER
    mock_verify_password.return_value = False

    with pytest.raises(HTTPException) as e:
        auth_service.login("testuser", "wrongpassword")
    assert e.value.status_code == 401
    assert "Invalid credentials" in e.value.detail
    mock_verify_password.assert_called_once_with("wrongpassword", SAMPLE_USER.hashed_password)
