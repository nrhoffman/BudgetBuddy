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
# get_by_id tests
# ---------------------------
@pytest.mark.parametrize(
    "db_return, expect_exception",
    [
        (True, False),   # found
        (False, True),   # not found
    ]
)
def test_get_by_id(repo, session, sample_user, db_return, expect_exception):
    mock_orm = MagicMock() if db_return else None
    session.query.return_value.filter.return_value.first.return_value = mock_orm

    if expect_exception:
        with pytest.raises(ValueError) as exc:
            repo.get_by_id("user_001")
        assert "not found" in str(exc.value)
    else:
        with patch("app.repositories.user_repository.orm_to_domain_user", return_value=sample_user):
            result = repo.get_by_id("user_001")
            assert result == sample_user

# ---------------------------
# get_by_username tests
# ---------------------------
@pytest.mark.parametrize(
    "db_return, expect_exception",
    [
        (True, False),   # found
        (False, True),   # not found
    ]
)
def test_get_by_username(repo, session, sample_user, db_return, expect_exception):
    mock_orm = MagicMock() if db_return else None
    session.query.return_value.filter.return_value.first.return_value = mock_orm

    if expect_exception:
        with pytest.raises(ValueError) as exc:
            repo.get_by_username("testuser")
        assert "not found" in str(exc.value)
    else:
        with patch("app.repositories.user_repository.orm_to_domain_user", return_value=sample_user):
            result = repo.get_by_username("testuser")
            assert result == sample_user

# ---------------------------
# add tests
# ---------------------------
@pytest.mark.parametrize(
    "side_effect",
    [
        None,                               # normal insert
        IntegrityError("msg", None, None),  # integrity error
        SQLAlchemyError("msg"),             # other SQLAlchemy error
    ]
)
def test_add(repo, session, sample_user, side_effect):
    """
    Since your current UserRepository.add does NOT call commit() or handle exceptions,
    we only need to test that session.add is called, and we simulate exceptions on add().
    """
    if side_effect:
        session.add.side_effect = side_effect
        with pytest.raises(type(side_effect)):
            repo.add(sample_user)
    else:
        repo.add(sample_user)
        session.add.assert_called_once()
