import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.routes.accounts import router, get_account_service, get_current_user
from app.models.transaction import UpdateTransaction
from fastapi import FastAPI

# --------------------------
# Setup TestClient with FastAPI app
# --------------------------
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# --------------------------
# Fixtures
# --------------------------
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
    # Override dependencies on the FastAPI app, not the router
    app.dependency_overrides[get_account_service] = lambda: mock_account_service
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    yield
    app.dependency_overrides.clear()

# --------------------------
# Tests
# --------------------------
@pytest.mark.parametrize(
    "accounts, expected_length",
    [
        ([], 0),
        ([{"id": "a1"}, {"id": "a2"}], 2),
    ],
)
def test_get_accounts_success(mock_account_service, mock_current_user, accounts, expected_length):
    mock_account_service.get_user_financial_snapshot.return_value = accounts
    response = client.get("/api/accounts/get-accounts")
    assert response.status_code == 200
    data = response.json()
    assert "accounts" in data
    assert len(data["accounts"]) == expected_length
    mock_account_service.get_user_financial_snapshot.assert_called_once_with(mock_current_user.id)

def test_get_accounts_exception(mock_account_service):
    mock_account_service.get_user_financial_snapshot.side_effect = Exception("fail")
    response = client.get("/api/accounts/get-accounts")
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to fetch accounts"

@pytest.mark.parametrize(
    "account_id, account_name",
    [("acc1", "NewName"), ("acc2", "AnotherName")]
)
def test_update_account_success(mock_account_service, mock_current_user, account_id, account_name):
    mock_account_service.update_account.return_value = {"updated": True}
    response = client.post(f"/api/accounts/update-account/{account_id}/{account_name}")
    assert response.status_code == 200
    assert response.json() == {"updated": True}
    mock_account_service.update_account.assert_called_once_with(
        account_id=account_id,
        user_id=mock_current_user.id,
        account_name=account_name
    )

def test_update_account_exception(mock_account_service):
    mock_account_service.update_account.side_effect = Exception("fail")
    response = client.post("/api/accounts/update-account/acc1/NewName")
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to update account"

@pytest.mark.parametrize("account_id", ["acc1", "acc2"])
def test_remove_account_success(mock_account_service, mock_current_user, account_id):
    mock_account_service.remove_account.return_value = {"removed": True}
    response = client.delete(f"/api/accounts/remove-account/{account_id}")
    assert response.status_code == 200
    assert response.json() == {"removed": True}
    mock_account_service.remove_account.assert_called_once_with(account_id, mock_current_user.id)

def test_remove_account_exception(mock_account_service):
    mock_account_service.remove_account.side_effect = Exception("fail")
    response = client.delete("/api/accounts/remove-account/acc1")
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to remove account"

# --------------------------
# Transaction update tests
# --------------------------
@pytest.mark.parametrize(
    "existing_tx, payload_data, expected_status",
    [
        ({"transaction_id": "tx1", "account_id": "acc1"}, {"name": "updated"}, "ok"),
    ]
)
def test_update_transaction_success(mock_account_service, mock_current_user, existing_tx, payload_data, expected_status):
    class MockTxn:
        account_id = existing_tx["account_id"]
        def model_copy(self, update=None):
            return {"transaction_id": "tx1", **(update or {})}

    mock_account_service.txn_repo.get_by_ids.return_value = [MockTxn()]
    mock_account_service.apply_transaction_changes = MagicMock()
    payload = UpdateTransaction(**payload_data)
    response = client.post(f"/api/accounts/{existing_tx['account_id']}/transactions/{existing_tx['transaction_id']}", json=payload.dict())
    assert response.status_code == 200
    assert response.json()["status"] == expected_status
    mock_account_service.apply_transaction_changes.assert_called_once()

@pytest.mark.parametrize(
    "existing_list, account_id",
    [
        ([], "acc1"),  # Transaction not found
        ([MagicMock(account_id="wrong_acc")], "acc1")  # Transaction does not belong
    ]
)
def test_update_transaction_404(mock_account_service, existing_list, account_id):
    mock_account_service.txn_repo.get_by_ids.return_value = existing_list
    payload = UpdateTransaction(name="test")
    response = client.post(f"/api/accounts/{account_id}/transactions/tx1", json=payload.dict())
    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"

def test_update_transaction_exception(mock_account_service):
    mock_account_service.txn_repo.get_by_ids.side_effect = Exception("fail")
    payload = UpdateTransaction(name="test")
    response = client.post("/api/accounts/acc1/transactions/tx1", json=payload.dict())
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to update transaction"
