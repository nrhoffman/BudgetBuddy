import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException
from app.services.auth_service import AuthService
from app.models.user import User

# --------------------------
# Fixtures
# --------------------------
@pytest.fixture
def mock_user_repo():
    return MagicMock()

@pytest.fixture
def auth_service(mock_user_repo):
    return AuthService(user_repo=mock_user_repo)

@pytest.fixture
def test_user():
    return User(
        id="user-123",
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpw",
        role="user"
    )

# --------------------------
# create_user tests
# --------------------------
@pytest.mark.parametrize(
    "exc_type, exc_msg, expected_status, expected_detail",
    [
        (None, None, 200, "User created successfully"),  # success
        (IntegrityError, "users_email_key", 409, "Email already exists"),
        (IntegrityError, "users_username_key", 409, "Username already exists"),
        (IntegrityError, "other_error", 400, "Invalid user data"),
        (SQLAlchemyError, None, 500, "Failed to create user"),
    ]
)
def test_create_user(auth_service, mock_user_repo, test_user, exc_type, exc_msg, expected_status, expected_detail):
    if exc_type is None:
        # normal success
        mock_user_repo.add.return_value = None
        result = auth_service.create_user(test_user)
        assert result["message"] == expected_detail
        assert result["user_id"] == test_user.id
    elif exc_type == IntegrityError:
        # simulate IntegrityError
        mock_exc = MagicMock()
        mock_exc.orig = exc_msg
        mock_user_repo.add.side_effect = IntegrityError(statement=None, params=None, orig=mock_exc.orig)
        with pytest.raises(HTTPException) as exc_info:
            auth_service.create_user(test_user)
        assert exc_info.value.status_code == expected_status
        assert exc_info.value.detail == expected_detail
    else:
        # simulate SQLAlchemyError
        mock_user_repo.add.side_effect = SQLAlchemyError("db error")
        with pytest.raises(HTTPException) as exc_info:
            auth_service.create_user(test_user)
        assert exc_info.value.status_code == expected_status
        assert exc_info.value.detail == expected_detail

# --------------------------
# login tests
# --------------------------
@pytest.mark.parametrize(
    "repo_return, pw_verify, expected_status, expected_detail",
    [
        ("user_found", True, 200, "Login successful"),   # success
        ("user_found", False, 401, "Invalid credentials"),  # invalid password
        (None, False, 401, "Invalid credentials"),  # user not found
        ("exception", None, 500, "Failed to authenticate user"),  # repo throws
    ]
)
def test_login(auth_service, mock_user_repo, test_user, repo_return, pw_verify, expected_status, expected_detail):
    if repo_return == "user_found":
        mock_user_repo.get_by_username.return_value = test_user
    elif repo_return is None:
        mock_user_repo.get_by_username.return_value = None
    else:  # simulate repo exception
        mock_user_repo.get_by_username.side_effect = Exception("db fail")

    with patch("app.services.auth_service.verify_password", return_value=pw_verify):
        with patch("app.services.auth_service.create_access_token", return_value="jwt-token"):
            if expected_status == 200:
                result = auth_service.login(test_user.username, "password")
                assert result["message"] == expected_detail
                assert result["access_token"] == "jwt-token"
                assert result["token_type"] == "bearer"
            else:
                with pytest.raises(HTTPException) as exc_info:
                    auth_service.login(test_user.username, "password")
                assert exc_info.value.status_code == expected_status
                assert exc_info.value.detail == expected_detail
