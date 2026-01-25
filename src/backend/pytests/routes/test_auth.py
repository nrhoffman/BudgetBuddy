import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from app.main import app
from app.routes import auth
from app.models.user import User, UserRole

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_auth_service():
    return MagicMock()

@pytest.fixture
def fake_user():
    return User(
        id=str(uuid4()),
        username="alice",
        email="alice@example.com",
        hashed_password="hashed_pw",
        role=UserRole.USER
    )

@pytest.fixture(autouse=True)
def override_dependencies(mock_auth_service, fake_user):
    app.dependency_overrides = {
        auth.get_auth_service: lambda: mock_auth_service,
        auth.get_current_user: lambda: fake_user,
    }
    yield
    auth.dependency_overrides = {}

# -----------------------
# Parametrized login
# -----------------------
@pytest.mark.parametrize(
    "login_data, expected_status, expected_response",
    [
        ({"username": "alice", "password": "pw123"}, 200, {"message": "Login successful", "access_token": "mock_token", "token_type": "bearer"}),
        ({"username": "bob", "password": "wrongpw"}, 401, {"detail": "Invalid credentials"}),
    ]
)
def test_login_param(test_client, mock_auth_service, login_data, expected_status, expected_response):
    if expected_status == 200:
        mock_auth_service.login.return_value = expected_response
    else:
        mock_auth_service.login.side_effect = HTTPException(status_code=401, detail="Invalid credentials")

    response = test_client.post("/api/auth/login", json=login_data)
    assert response.status_code == expected_status
    assert response.json() == expected_response

# -----------------------
# Parametrized sign-up
# -----------------------
@pytest.mark.parametrize(
    "user_data",
    [
        {"username": "alice", "email": "alice@example.com", "password": "pw123", "role": "user"},
        {"username": "bob", "email": "bob@example.com", "password": "pw456", "role": "admin"},
    ]
)
def test_sign_up_param(test_client, mock_auth_service, user_data):
    created_user = User(
        id=str(uuid4()),
        username=user_data["username"],
        email=user_data["email"],
        hashed_password="hashed_pw",
        role=UserRole(user_data["role"])
    )
    mock_auth_service.create_user.return_value = created_user

    response = test_client.post("/api/auth/sign-up", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert data["role"] == user_data["role"]
    UUID(data["id"])
# -----------------------
# Check-login (authenticated)
# -----------------------
def test_check_login_authenticated(test_client):
    response = test_client.post("/api/auth/check-login")
    assert response.status_code == 200
    assert response.json() == {"message": "success"}
