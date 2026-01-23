import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.models.user import User, UserRole
from app.models.account import Account
from app.main import app
from app.routes import accounts

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_budget_service():
    return MagicMock()

@pytest.fixture
def fake_user():
    return User(
        id="user_001",
        username="alice",
        email="alice@example.com",
        hashed_password="hashed_pw",
        role=UserRole.USER
    )

@pytest.fixture(autouse=True)
def override_dependencies(mock_budget_service, fake_user):
    app.dependency_overrides = {
        accounts.get_budget_service: lambda: mock_budget_service,
        accounts.get_current_user: lambda: fake_user,
    }
    yield
    app.dependency_overrides = {}


# -----------------------
# Parametrized get accounts
# -----------------------
@pytest.mark.parametrize(
    "accounts_data, expected_count",
    [
        ([], 0),
        ([Account(id="acc_001", name="Checking", type="depository", subtype=None, balance=1000.0, transactions=[])], 1),
        ([Account(id="acc_001", name="Checking", type="depository", subtype=None, balance=1000.0, transactions=[]),
          Account(id="acc_002", name="Savings", type="depository", subtype=None, balance=5000.0, transactions=[])], 2),
    ]
)
def test_get_accounts_param(test_client, mock_budget_service, accounts_data, expected_count):
    mock_budget_service.get_user_financial_snapshot.return_value = accounts_data
    response = test_client.get("/api/accounts/get-accounts")
    assert response.status_code == 200
    data = response.json()
    assert len(data["accounts"]) == expected_count

# -----------------------
# Parametrized remove account
# -----------------------
@pytest.mark.parametrize(
    "account_id, side_effect, expected_status",
    [
        ("acc_001", None, 200),
        ("nonexistent", None, 404),
    ]
)
def test_remove_account_param(test_client, mock_budget_service, account_id, side_effect, expected_status):
    mock_budget_service.remove_account.return_value = {"message": "Account deleted successfully"}
    
    if account_id == "nonexistent":
        from fastapi import HTTPException
        mock_budget_service.remove_account.side_effect = HTTPException(status_code=404, detail="Account not found")
    
    response = test_client.delete(f"/api/accounts/remove-account/{account_id}")
    assert response.status_code == expected_status
