import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.repositories.user_repository import UserRepository
from app.models.user import User

# ---------------------------
# Fixtures
# ---------------------------
@pytest.fixture
def session():
    return MagicMock()

@pytest.fixture
def repo(session):
    return UserRepository(session)

@pytest.fixture
def sample_user():
    return User(
        id="user_001",
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpwd",
        role="user"
    )

# ---------------------------
# get_by_id
# ---------------------------
@pytest.mark.parametrize(
    "db_return, expect_exception",
    [
        (MagicMock(), False),  # normal
        (None, True),          # not found
        ("raise", True),       # SQLAlchemyError
    ]
)
def test_get_by_id(repo, session, sample_user, db_return, expect_exception):
    if db_return == "raise":
        session.query.return_value.filter.return_value.first.side_effect = SQLAlchemyError()
        with pytest.raises(RuntimeError):
            repo.get_by_id("user_001")
    elif expect_exception:
        session.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            repo.get_by_id("user_001")
    else:
        session.query.return_value.filter.return_value.first.return_value = MagicMock()
        with patch("app.repositories.user_repository.orm_to_domain_user", return_value=sample_user):
            result = repo.get_by_id("user_001")
            assert result == sample_user

# ---------------------------
# get_by_username
# ---------------------------
@pytest.mark.parametrize(
    "db_return, expect_exception",
    [
        (MagicMock(), False),  # normal
        (None, True),          # not found
        ("raise", True),       # SQLAlchemyError
    ]
)
def test_get_by_username(repo, session, sample_user, db_return, expect_exception):
    if db_return == "raise":
        session.query.return_value.filter.return_value.first.side_effect = SQLAlchemyError()
        with pytest.raises(RuntimeError):
            repo.get_by_username("testuser")
    elif expect_exception:
        session.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            repo.get_by_username("testuser")
    else:
        session.query.return_value.filter.return_value.first.return_value = MagicMock()
        with patch("app.repositories.user_repository.orm_to_domain_user", return_value=sample_user):
            result = repo.get_by_username("testuser")
            assert result == sample_user

# ---------------------------
# add
# ---------------------------
@pytest.mark.parametrize(
    "raise_exc, expected_exception",
    [
        (None, None),                  # normal insert
        (IntegrityError("msg", None, None), ValueError),  # unique constraint
        (SQLAlchemyError("msg"), RuntimeError),          # other db error
    ]
)
def test_add(repo, session, sample_user, raise_exc, expected_exception):
    if raise_exc:
        session.add.side_effect = raise_exc
        session.commit.side_effect = raise_exc
        with pytest.raises(expected_exception):
            repo.add(sample_user)
    else:
        repo.add(sample_user)
        session.add.assert_called_once()
        session.commit.assert_called_once()
