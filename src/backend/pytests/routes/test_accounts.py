import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.models.user import User, UserRole
from app.models.account import Account
from app.main import app
from app.routes import accounts


# -----------------------
# Fixtures
# -----------------------
@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def mock_account_service():
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
def override_dependencies(mock_account_service, fake_user):
    """
    Override dependencies globally for all tests in this module.
    """
    app.dependency_overrides = {
        accounts.get_account_service: lambda: mock_account_service,
        accounts.get_current_user: lambda: fake_user,
    }
    yield
    app.dependency_overrides = {}


# -----------------------
# GET /get-accounts
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
def test_get_accounts_param(test_client, mock_account_service, accounts_data, expected_count):
    mock_account_service.get_user_financial_snapshot.return_value = accounts_data

    response = test_client.get("/api/accounts/get-accounts")
    assert response.status_code == 200

    data = response.json()
    assert "accounts" in data
    assert len(data["accounts"]) == expected_count
    mock_account_service.get_user_financial_snapshot.assert_called_once_with("user_001")


# -----------------------
# POST /update-account/{account_id}/{account_name}
# -----------------------
def test_update_account_success(test_client, mock_account_service):
    mock_account_service.update_account.return_value = {"message": "Updated successfully"}

    response = test_client.post("/api/accounts/update-account/acc_001/NewName")
    assert response.status_code == 200
    data = response.json()
    assert data == {"message": "Updated successfully"}
    mock_account_service.update_account.assert_called_once_with(
        account_id="acc_001",
        user_id="user_001",
        account_name="NewName"
    )


def test_update_account_failure(test_client, mock_account_service):
    from fastapi import HTTPException
    mock_account_service.update_account.side_effect = HTTPException(status_code=404, detail="Account not found")

    response = test_client.post("/api/accounts/update-account/nonexistent/NewName")
    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"
    mock_account_service.update_account.assert_called_once_with(
        account_id="nonexistent",
        user_id="user_001",
        account_name="NewName"
    )


# -----------------------
# DELETE /remove-account/{account_id}
# -----------------------
def test_remove_account_success(test_client, mock_account_service):
    mock_account_service.remove_account.return_value = {"message": "Account deleted successfully"}

    response = test_client.delete("/api/accounts/remove-account/acc_001")
    assert response.status_code == 200
    assert response.json() == {"message": "Account deleted successfully"}
    mock_account_service.remove_account.assert_called_once_with("acc_001", "user_001")


def test_remove_account_not_found(test_client, mock_account_service):
    from fastapi import HTTPException
    mock_account_service.remove_account.side_effect = HTTPException(status_code=404, detail="Account not found")

    response = test_client.delete("/api/accounts/remove-account/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"
    mock_account_service.remove_account.assert_called_once_with("nonexistent", "user_001")
