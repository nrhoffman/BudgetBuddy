import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.services.auth_service import AuthService
from app.models.user import User
from app.exceptions import ConflictError, ValidationError, DatabaseError, AuthenticationError

# ---------------------------
# Fixtures
# ---------------------------
@pytest.fixture
def mock_user_repo():
    return MagicMock()


@pytest.fixture
def auth_service(mock_user_repo):
    return AuthService(user_repo=mock_user_repo)


@pytest.fixture
def test_user():
    return User(
        id="user-123",
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpw",
        role="user"
    )


# ---------------------------
# create_user tests
# ---------------------------
@pytest.mark.parametrize(
    "exc_type,exc_msg,expected_exception",
    [
        (None, None, None),                       # success
        (IntegrityError, "users_email_key", ConflictError),
        (IntegrityError, "users_username_key", ConflictError),
        (IntegrityError, "other_error", ValidationError),
        (SQLAlchemyError, None, DatabaseError),
    ]
)
def test_create_user(auth_service, mock_user_repo, test_user, exc_type, exc_msg, expected_exception):
    if exc_type is None:
        # normal success
        mock_user_repo.add.return_value = None
        result = auth_service.create_user(test_user)
        assert result == test_user.id
    elif exc_type == IntegrityError:
        # simulate IntegrityError
        mock_exc = MagicMock()
        mock_exc.orig = exc_msg
        mock_user_repo.add.side_effect = IntegrityError(statement=None, params=None, orig=mock_exc.orig)
        with pytest.raises(expected_exception):
            auth_service.create_user(test_user)
    else:
        # simulate SQLAlchemyError
        mock_user_repo.add.side_effect = SQLAlchemyError("db error")
        with pytest.raises(expected_exception):
            auth_service.create_user(test_user)


# ---------------------------
# login tests
# ---------------------------
@pytest.mark.parametrize(
    "repo_return,pw_verify,expected_exception",
    [
        ("user_found", True, None),             # success
        ("user_found", False, AuthenticationError),   # wrong password
        (None, False, AuthenticationError),           # user not found
        ("exception", None, DatabaseError),           # repo throws
    ]
)
def test_login(auth_service, mock_user_repo, test_user, repo_return, pw_verify, expected_exception):
    if repo_return == "user_found":
        mock_user_repo.get_by_username.return_value = test_user
    elif repo_return is None:
        mock_user_repo.get_by_username.return_value = None
    else:  # simulate repo exception
        from sqlalchemy.exc import SQLAlchemyError
        mock_user_repo.get_by_username.side_effect = SQLAlchemyError("db fail")

    with patch("app.services.auth_service.verify_password", return_value=pw_verify):
        with patch("app.services.auth_service.create_access_token", return_value="jwt-token"):
            if expected_exception:
                with pytest.raises(expected_exception):
                    auth_service.login(test_user.username, "password")
            else:
                token = auth_service.login(test_user.username, "password")
                assert token == "jwt-token"
