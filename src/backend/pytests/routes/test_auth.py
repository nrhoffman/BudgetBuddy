import pytest
from fastapi import HTTPException
from unittest.mock import Mock

from app.routes.auth import login, create_user, check_login
from app.models.user import User, UserCreate
from app.models.auth import LoginRequest


# ---------------------------
# Test data and fixtures
# ---------------------------

@pytest.fixture
def mock_auth_service():
    return Mock()


@pytest.fixture
def test_user_create():
    return UserCreate(username="testuser", email="test@example.com", password="secret", role="user")


@pytest.fixture
def test_user():
    return User(
        id="123",
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_secret",
        role="user",
    )


# ---------------------------
# login endpoint tests
# ---------------------------

@pytest.mark.parametrize(
    "username,password,expected_result,raises_exception",
    [
        ("validuser", "validpass", {"token": "abc"}, False),
        ("invaliduser", "wrongpass", None, True),
    ],
)
def test_login(username, password, expected_result, raises_exception, mock_auth_service):
    req = LoginRequest(username=username, password=password)

    if raises_exception:
        mock_auth_service.login.side_effect = Exception("Invalid credentials")
        with pytest.raises(HTTPException) as exc:
            login(req, auth_service=mock_auth_service)
        assert exc.value.status_code == 401
        assert "Invalid credentials" in exc.value.detail
    else:
        mock_auth_service.login.return_value = expected_result
        result = login(req, auth_service=mock_auth_service)
        assert result == expected_result
        mock_auth_service.login.assert_called_once_with(username=username, password=password)


# ---------------------------
# create_user endpoint tests
# ---------------------------

@pytest.mark.parametrize("raises_exception", [False, True])
def test_create_user(test_user_create, test_user, mock_auth_service, raises_exception):
    if raises_exception:
        mock_auth_service.create_user.side_effect = Exception("Creation failed")
        with pytest.raises(HTTPException) as exc:
            create_user(test_user_create, auth_service=mock_auth_service)
        assert exc.value.status_code == 500
        assert "Failed to create user" in exc.value.detail
    else:
        mock_auth_service.create_user.return_value = test_user
        result = create_user(test_user_create, auth_service=mock_auth_service)
        assert result == test_user
        mock_auth_service.create_user.assert_called_once()
        assert result.username == test_user_create.username


# ---------------------------
# check_login endpoint tests
# ---------------------------

@pytest.mark.parametrize(
    "current_user,expected_status,raises_exception",
    [
        (User(id="1", username="u1", email="u1@test.com", hashed_password="x", role="user"), 200, False),
        (None, None, True),
    ],
)
def test_check_login(current_user, expected_status, raises_exception):
    if raises_exception:
        with pytest.raises(HTTPException) as exc:
            check_login(_current_user=current_user)
        assert exc.value.status_code == 401
        assert "Not authenticated" in exc.value.detail
    else:
        result = check_login(_current_user=current_user)
        assert result == {"message": "success"}
