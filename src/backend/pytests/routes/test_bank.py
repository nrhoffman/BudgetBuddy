import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.routes import bank
from app.models.exchange_token import ExchangeToken

# ----------------------------
# Fixtures
# ----------------------------
class DummyUser:
    def __init__(self, user_id="user123"):
        self.id = user_id


class DummyBankingService:
    def __init__(self):
        self.called = {}

    def create_bank_link_token(self, user_id):
        self.called["link_token"] = user_id
        if user_id == "fail":
            raise Exception("Token failure")
        return f"token_for_{user_id}"

    def add_bank_accounts(self, user_id, public_token, institution_id, institution_name):
        self.called["exchange_token"] = {
            "user_id": user_id,
            "public_token": public_token,
            "institution_id": institution_id,
            "institution_name": institution_name,
        }
        if public_token == "fail":
            raise Exception("Exchange failure")

    def plaid_webhook(self, payload):
        self.called["webhook"] = payload
        if payload.get("fail"):
            raise Exception("Webhook failure")
        return {"status": "ok"}


@pytest.fixture
def dummy_user():
    return DummyUser()


@pytest.fixture
def dummy_service():
    return DummyBankingService()


@pytest.fixture
def client(dummy_service, dummy_user):
    from fastapi import Depends, FastAPI

    app = FastAPI()
    app.include_router(bank.router)

    # Override dependencies
    app.dependency_overrides[bank.get_banking_service] = lambda: dummy_service
    app.dependency_overrides[bank.get_current_user] = lambda: dummy_user
    return TestClient(app)


# ----------------------------
# Tests for /create-link-token
# ----------------------------
@pytest.mark.parametrize("user_id,expected_token,should_fail", [
    ("user123", "token_for_user123", False),
    ("fail", None, True),
])
def test_create_link_token(client, dummy_user, dummy_service, user_id, expected_token, should_fail):
    dummy_user.id = user_id
    if should_fail:
        response = client.post("/api/bank/create-link-token")
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to create link token"
    else:
        response = client.post("/api/bank/create-link-token")
        assert response.status_code == 200
        assert response.json() == {"link_token": expected_token}
        assert dummy_service.called["link_token"] == user_id


# ----------------------------
# Tests for /exchange-token
# ----------------------------
@pytest.mark.parametrize("public_token,institution_id,institution_name,should_fail", [
    ("token123", "inst1", "Bank A", False),
    ("fail", "inst2", "Bank B", True),
])
def test_exchange_token(client, dummy_service, dummy_user,
                        public_token, institution_id, institution_name, should_fail):
    payload = {
        "public_token": public_token,
        "institution_id": institution_id,
        "institution_name": institution_name,
    }
    if should_fail:
        response = client.post("/api/bank/exchange-token", json=payload)
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to exchange token"
    else:
        response = client.post("/api/bank/exchange-token", json=payload)
        assert response.status_code == 200
        assert response.json() == {"message": "Bank accounts synced"}
        called = dummy_service.called["exchange_token"]
        assert called["user_id"] == dummy_user.id
        assert called["public_token"] == public_token
        assert called["institution_id"] == institution_id
        assert called["institution_name"] == institution_name
