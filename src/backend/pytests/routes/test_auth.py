import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
from fastapi import FastAPI
from app.models.user import UserCreate, User
from app.models.auth import LoginRequest
from app.exceptions import AuthenticationError, ConflictError
from app.routes.auth import router as auth_router
from app.dependencies import get_auth_service, get_current_user

# --------------------------
# Setup TestClient
# --------------------------
@pytest.fixture
def mock_auth_service():
    return Mock()

@pytest.fixture
def mock_current_user():
    user = Mock(spec=User)
    user.id = "user_123"
    user.username = "testuser"
    return user

@pytest.fixture
def client(mock_auth_service, mock_current_user):
    app = FastAPI()
    app.include_router(auth_router)

    # Override dependencies
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    return TestClient(app)

@pytest.fixture
def test_user_create():
    return UserCreate(username="testuser", email="test@example.com", password="secret", role="user")


# --------------------------
# login endpoint tests
# --------------------------
@pytest.mark.parametrize(
    "username,password,service_return,service_side_effect,expected_exception",
    [
        ("validuser", "validpass", "token123", None, None),  # success
        ("invaliduser", "wrongpass", None, AuthenticationError("Invalid credentials"), AuthenticationError),  # failure
    ]
)
def test_login(client, mock_auth_service, username, password, service_return, service_side_effect, expected_exception):
    if service_side_effect:
        mock_auth_service.login.side_effect = service_side_effect
    else:
        mock_auth_service.login.return_value = service_return

    if expected_exception:
        with pytest.raises(expected_exception) as exc:
            client.post("/api/auth/login", json={"username": username, "password": password})
        assert str(exc.value) == str(service_side_effect)
    else:
        response = client.post("/api/auth/login", json={"username": username, "password": password})
        data = response.json()
        assert response.status_code == 200
        assert data["access_token"] == service_return
        assert data["token_type"] == "bearer"
        assert data["message"] == "Login successful"


# --------------------------
# create_user endpoint tests
# --------------------------
@pytest.mark.parametrize(
    "service_return,service_side_effect,expected_exception",
    [
        ("123", None, None),  # success
        (None, ConflictError("Username already exists"), ConflictError),  # failure
    ]
)
def test_create_user(client, mock_auth_service, test_user_create, service_return, service_side_effect, expected_exception):
    if service_side_effect:
        mock_auth_service.create_user.side_effect = service_side_effect
    else:
        mock_auth_service.create_user.return_value = service_return

    if expected_exception:
        with pytest.raises(expected_exception) as exc:
            client.post("/api/auth/sign-up", json=test_user_create.model_dump())
        assert str(exc.value) == str(service_side_effect)
    else:
        response = client.post("/api/auth/sign-up", json=test_user_create.model_dump())
        data = response.json()
        assert response.status_code == 200
        assert data["user_id"] == service_return
        assert data["message"] == "User created successfully"


# --------------------------
# check_login endpoint tests
# --------------------------
@pytest.mark.parametrize(
    "current_user,expected_exception",
    [
        (Mock(spec=User, id="1", username="u1"), None),  # authenticated
        (None, AuthenticationError),  # unauthenticated
    ]
)
def test_check_login(client, current_user, expected_exception):
    # Override dependency
    client.app.dependency_overrides[get_current_user] = lambda: current_user

    if expected_exception:
        with pytest.raises(expected_exception) as exc:
            client.post("/api/auth/check-login")
        assert str(exc.value) == "Not authenticated"
    else:
        response = client.post("/api/auth/check-login")
        data = response.json()
        assert response.status_code == 200
        assert data["message"] == "success"
