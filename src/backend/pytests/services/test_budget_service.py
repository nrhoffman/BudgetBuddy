import pytest
from unittest.mock import MagicMock

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.services.budget_service import BudgetService
from app.models.user import User, UserRole
from app.models.account import Account
from app.models.transaction import Transaction


# ---------- Fixtures ----------

@pytest.fixture
def session():
    return MagicMock()


@pytest.fixture
def user_repo():
    return MagicMock()


@pytest.fixture
def account_repo():
    return MagicMock()


@pytest.fixture
def banking_provider():
    return MagicMock()


@pytest.fixture
def service(session, user_repo, account_repo, banking_provider):
    return BudgetService(
        session=session,
        user_repo=user_repo,
        account_repo=account_repo,
        banking_provider=banking_provider,
    )


@pytest.fixture
def fake_user():
    return User(
        id="user_001",
        username="alice",
        email="alice@example.com",
        hashed_password="hashed_pw",
        role=UserRole.USER,
    )


# ---------- Auth / Login ----------

@pytest.mark.parametrize(
    "user_found, password_valid, should_fail",
    [
        (True, True, False),
        (True, False, True),
        (False, False, True),
    ],
)
def test_login_param(
    service,
    user_repo,
    fake_user,
    monkeypatch,
    user_found,
    password_valid,
    should_fail,
):
    user_repo.get_by_username.return_value = fake_user if user_found else None

    monkeypatch.setattr(
        "app.services.budget_service.verify_password",
        lambda pw, hpw: password_valid,
    )
    monkeypatch.setattr(
        "app.services.budget_service.create_access_token",
        lambda subject: "fake-token",
    )

    if should_fail:
        with pytest.raises(HTTPException) as exc:
            service.login("alice", "pw")

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.value.detail == "Invalid credentials"
    else:
        result = service.login("alice", "pw")

        assert result["access_token"] == "fake-token"
        assert result["token_type"] == "bearer"
        assert result["message"] == "Login successful"


# ---------- User Creation ----------

@pytest.mark.parametrize(
    "exception_msg, expected_status, expected_detail",
    [
        ("users_email_key", status.HTTP_409_CONFLICT, "Email already exists"),
        ("users_username_key", status.HTTP_409_CONFLICT, "Username already exists"),
        ("something_else", status.HTTP_400_BAD_REQUEST, "Invalid user data"),
    ],
)
def test_create_user_integrity_errors(
    service,
    user_repo,
    session,
    fake_user,
    exception_msg,
    expected_status,
    expected_detail,
):
    user_repo.add.side_effect = IntegrityError(
        statement=None,
        params=None,
        orig=exception_msg,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_user(fake_user)

    session.rollback.assert_called_once()
    assert exc.value.status_code == expected_status
    assert exc.value.detail == expected_detail


def test_create_user_success(service, user_repo, fake_user):
    result = service.create_user(fake_user)

    user_repo.add.assert_called_once_with(fake_user)
    assert result["message"] == "User created successfully"
    assert result["user_id"] == fake_user.id


# ---------- User Retrieval ----------

@pytest.mark.parametrize(
    "user_found, should_fail",
    [
        (True, False),
        (False, True),
    ],
)
def test_get_user_param(service, user_repo, fake_user, user_found, should_fail):
    user_repo.get_by_id.return_value = fake_user if user_found else None

    if should_fail:
        with pytest.raises(HTTPException) as exc:
            service.get_user("user_001")

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    else:
        user = service.get_user("user_001")
        assert user.id == fake_user.id


# ---------- Accounts ----------

def test_create_account_success(service, account_repo):
    account = MagicMock(spec=Account)
    account.id = "acc_001"

    result = service.create_account(account, "user_001")

    account_repo.add_account.assert_called_once_with(account, "user_001")
    assert result["account_id"] == "acc_001"


@pytest.mark.parametrize(
    "account_found, should_fail",
    [
        (True, False),
        (False, True),
    ],
)
def test_get_account_param(service, account_repo, account_found, should_fail):
    account = MagicMock(spec=Account)
    account_repo.get.return_value = account if account_found else None

    if should_fail:
        with pytest.raises(HTTPException) as exc:
            service.get_account("acc", "user")

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    else:
        result = service.get_account("acc", "user")
        assert result == account


# ---------- Transactions ----------

@pytest.mark.parametrize(
    "account_exists, should_fail",
    [
        (True, False),
        (False, True),
    ],
)
def test_add_transaction_param(service, account_repo, account_exists, should_fail):
    account = MagicMock()
    account.transactions = []

    account_repo.get.return_value = account if account_exists else None

    txn = MagicMock(spec=Transaction)
    txn.transaction_id = "txn_001"

    if should_fail:
        with pytest.raises(HTTPException) as exc:
            service.add_transaction("user", "acc", txn)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    else:
        result = service.add_transaction("user", "acc", txn)

        assert result["transaction_id"] == "txn_001"
        assert txn in account.transactions


# ---------- Banking / Plaid ----------

@pytest.mark.parametrize(
    "provider_present, should_fail",
    [
        (True, False),
        (False, True),
    ],
)
def test_create_bank_link_token_param(service, provider_present, should_fail):
    if not provider_present:
        service.banking_provider = None

    if should_fail:
        with pytest.raises(HTTPException) as exc:
            service.create_bank_link_token("user")

        assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        service.banking_provider.create_link_token.return_value = "link-token"

        token = service.create_bank_link_token("user")
        assert token == "link-token"


def test_add_bank_accounts_success(service, banking_provider):
    account = MagicMock(spec=Account)
    account.id = "acc_001"

    txn = MagicMock(spec=Transaction)
    txn.transaction_id = "txn_001"

    banking_provider.exchange_public_token.return_value = "access-token"
    banking_provider.get_accounts.return_value = [account]
    banking_provider.get_transactions.return_value = [txn]

    result = service.add_bank_accounts("user_001", "public-token")

    assert result["status"] == "linked"
    assert result["accounts_added"] == 1
