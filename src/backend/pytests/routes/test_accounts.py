import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from fastapi import FastAPI

from app.routes.accounts import router
from app.dependencies import get_account_service, get_current_user
from app.models.transaction import UpdateTransaction

# --------------------------
# Setup TestClient with FastAPI app
# --------------------------
app = FastAPI()
app.include_router(router)

@pytest.fixture
def mock_account_service():
    return MagicMock()

@pytest.fixture
def mock_current_user():
    user = MagicMock()
    user.id = "user_123"
    return user

@pytest.fixture(autouse=True)
def override_dependencies(mock_account_service, mock_current_user):
    app.dependency_overrides[get_account_service] = lambda: mock_account_service
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def client():
    return TestClient(app)


# --------------------------
# get_accounts tests
# --------------------------
@pytest.mark.parametrize(
    "accounts, service_return",
    [
        ([], []),
        ([{"id": "a1"}, {"id": "a2"}], [{"id": "a1"}, {"id": "a2"}]),
    ]
)
def test_get_accounts(client, mock_account_service, accounts, service_return):
    mock_account_service.get_user_financial_snapshot.return_value = service_return
    response = client.get("/api/accounts/get-accounts")
    assert response.status_code == 200
    data = response.json()
    assert "accounts" in data
    assert data["accounts"] == accounts


# --------------------------
# update_account tests
# --------------------------
@pytest.mark.parametrize(
    "account_id, account_name",
    [
        ("acc1", "NewName"),
        ("acc2", "AnotherName"),
    ]
)
def test_update_account(client, mock_account_service, account_id, account_name):
    mock_account_service.update_account.return_value = None
    response = client.post(f"/api/accounts/update-account/{account_id}/{account_name}")
    assert response.status_code == 200
    assert response.json() == {"message": "Account updated successfully"}
    mock_account_service.update_account.assert_called_once_with(
        account_id=account_id,
        user_id="user_123",
        account_name=account_name
    )
    mock_account_service.update_account.reset_mock()


# --------------------------
# remove_account tests
# --------------------------
@pytest.mark.parametrize("account_id", ["acc1", "acc2"])
def test_remove_account(client, mock_account_service, account_id):
    mock_account_service.remove_account.return_value = None
    response = client.delete(f"/api/accounts/remove-account/{account_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Account deleted successfully"}
    mock_account_service.remove_account.assert_called_once_with(account_id, "user_123")
    mock_account_service.remove_account.reset_mock()


# --------------------------
# update_transaction tests
# --------------------------
@pytest.mark.parametrize(
    "payload_data",
    [
        ({"name": "updated"}),
        ({"name": "another_update"}),
    ]
)
def test_update_transaction(client, mock_account_service, payload_data):
    mock_account_service.update_transaction.return_value = None
    payload = UpdateTransaction(**payload_data)
    response = client.post(f"/api/accounts/acc1/transactions/tx1", json=payload.model_dump())
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    mock_account_service.update_transaction.assert_called_once()
    mock_account_service.update_transaction.reset_mock()


# --------------------------
# get_institutions tests
# --------------------------
@pytest.mark.parametrize(
    "institutions",
    [
        [],
        [{"id": "inst1"}, {"id": "inst2"}],
    ]
)
def test_get_institutions(client, mock_account_service, institutions):
    mock_account_service.get_institutions.return_value = institutions
    response = client.get("/api/accounts/get-institutions")
    assert response.status_code == 200
    assert response.json() == institutions
