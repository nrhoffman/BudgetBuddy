import pytest
from fastapi import HTTPException, status
from unittest.mock import MagicMock

from app.dependencies import get_current_user
from app.models.user import User, UserRole


@pytest.mark.parametrize(
    "jwt_payload, user_found, expected_exception",
    [
        ({"sub": "user_001"}, True, None),
        ({"sub": None}, False, status.HTTP_401_UNAUTHORIZED),
        ({}, False, status.HTTP_401_UNAUTHORIZED),
    ],
)
def test_get_current_user_param(
    jwt_payload,
    user_found,
    expected_exception,
    monkeypatch,
):
    fake_user = User(
        id="user_001",
        username="alice",
        email="alice@example.com",
        hashed_password="hashed",
        role=UserRole.USER,
    )

    monkeypatch.setattr(
        "app.dependencies.decode_jwt",
        lambda _: jwt_payload
    )

    mock_db = MagicMock()
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = fake_user if user_found else None

    monkeypatch.setattr(
        "app.dependencies.UserRepository",
        lambda db: mock_repo
    )

    if expected_exception:
        with pytest.raises(HTTPException) as exc:
            get_current_user(token="fake-token", db=mock_db)
        assert exc.value.status_code == expected_exception
    else:
        user = get_current_user(token="fake-token", db=mock_db)
        assert user.id == "user_001"
