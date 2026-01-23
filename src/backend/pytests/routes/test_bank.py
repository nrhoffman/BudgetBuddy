import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from uuid import uuid4

from app.main import app
from app.routes import bank
from app.models.user import User, UserRole
from app.schemas.bank import ExchangeTokenRequest

# -----------------------
# Fixtures
# -----------------------
@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_budget_service():
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

# Override dependencies automatically
@pytest.fixture(autouse=True)
def override_dependencies(mock_budget_service, fake_user):
    app.dependency_overrides = {
        bank.get_budget_service: lambda: mock_budget_service,
        bank.get_current_user: lambda: fake_user,
    }
    yield
    app.dependency_overrides = {}

# -----------------------
# Parametrized create-link-token
# -----------------------
@pytest.mark.parametrize(
    "mock_token",
    [
        "link_token_123",
        "link_token_abc",
        "link_token_xyz"
    ]
)
def test_create_link_token_param(test_client, mock_budget_service, fake_user, mock_token):
    mock_budget_service.create_bank_link_token.return_value = mock_token

    response = test_client.post("/api/bank/create-link-token")
    assert response.status_code == 200
    data = response.json()
    assert "link_token" in data
    assert data["link_token"] == mock_token
    mock_budget_service.create_bank_link_token.assert_called_once_with(fake_user.id)

# -----------------------
# Parametrized exchange-token
# -----------------------
@pytest.mark.parametrize(
    "public_token, expected_message",
    [
        ("public_token_001", "Bank accounts synced"),
        ("public_token_abc", "Bank accounts synced"),
        ("public_token_xyz", "Bank accounts synced"),
    ]
)
def test_exchange_token_param(test_client, mock_budget_service, fake_user, public_token, expected_message):
    payload = {"public_token": public_token}
    response = test_client.post("/api/bank/exchange-token", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == expected_message
    mock_budget_service.add_bank_accounts.assert_called_once_with(fake_user.id, public_token)
