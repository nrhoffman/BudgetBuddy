import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.db.base import Base
from app.db.user_orm import UserORM
from app.repositories.user_repository import UserRepository
from app.models.user import User, UserRole


# -----------------------
# Fixture: in-memory DB session
# -----------------------
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# -----------------------
# Fixture: repository
# -----------------------
@pytest.fixture
def repo(db_session):
    return UserRepository(db_session)


# -----------------------
# Parametrized test: adding and retrieving users by ID
# -----------------------
@pytest.mark.parametrize(
    "user_data",
    [
        {"id": "user_001", "username": "alice", "email": "alice@example.com", "hashed_password": "hashed_pw_123", "role": UserRole.USER},
        {"id": "user_002", "username": "bob", "email": "bob@example.com", "hashed_password": "hashed_pw_456", "role": UserRole.ADMIN},
    ]
)
def test_add_and_get_user_by_id_param(repo, user_data):
    user = User(**user_data)
    repo.add(user)
    
    fetched_user = repo.get_by_id(user.id)
    assert isinstance(fetched_user, User)
    for field in ["id", "username", "email", "hashed_password", "role"]:
        assert getattr(fetched_user, field) == user_data[field]


# -----------------------
# Parametrized test: retrieving users by username
# -----------------------
@pytest.mark.parametrize(
    "user_data",
    [
        {"id": "user_003", "username": "carol", "email": "carol@example.com", "hashed_password": "pw_789", "role": UserRole.USER},
        {"id": "user_004", "username": "dave", "email": "dave@example.com", "hashed_password": "pw_000", "role": UserRole.ADMIN},
    ]
)
def test_get_user_by_username_param(repo, user_data):
    user = User(**user_data)
    repo.add(user)

    fetched_user = repo.get_by_username(user.username)
    assert isinstance(fetched_user, User)
    assert fetched_user.id == user_data["id"]
    assert fetched_user.username == user_data["username"]
    assert fetched_user.role == user_data["role"]


# -----------------------
# Parametrized test: retrieving non-existent users
# -----------------------
@pytest.mark.parametrize(
    "lookup_id, lookup_username",
    [
        ("nonexistent", "ghost"),
        ("missing", "phantom"),
    ]
)
def test_get_nonexistent_user_param(repo, lookup_id, lookup_username):
    with pytest.raises(ValueError) as excinfo:
        repo.get_by_id(lookup_id)
    assert lookup_id in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        repo.get_by_username(lookup_username)
    assert lookup_username in str(excinfo.value)


# -----------------------
# Parametrized test: handling unique constraint violations
# -----------------------
@pytest.mark.parametrize(
    "users_data",
    [
        [
            {"id": "user_005", "username": "eve", "email": "eve@example.com", "hashed_password": "pw_111", "role": UserRole.USER},
            {"id": "user_006", "username": "eve", "email": "eve2@example.com", "hashed_password": "pw_222", "role": UserRole.ADMIN},
        ],
        [
            {"id": "user_007", "username": "frank", "email": "frank@example.com", "hashed_password": "pw_333", "role": UserRole.USER},
            {"id": "user_008", "username": "frank", "email": "frank2@example.com", "hashed_password": "pw_444", "role": UserRole.ADMIN},
        ]
    ]
)
def test_add_duplicate_user_param(repo, users_data):
    user1 = User(**users_data[0])
    user2 = User(**users_data[1])

    repo.add(user1)
    with pytest.raises(ValueError) as excinfo:
        repo.add(user2)
    assert "Integrity error creating user" in str(excinfo.value)


# -----------------------
# Parametrized test: generic SQLAlchemy error handling
# -----------------------
@pytest.mark.parametrize(
    "user_data",
    [
        {"id": "user_009", "username": "gina", "email": "gina@example.com", "hashed_password": "pw_555", "role": UserRole.USER},
        {"id": "user_010", "username": "henry", "email": "henry@example.com", "hashed_password": "pw_666", "role": UserRole.ADMIN},
    ]
)
def test_add_sqlalchemy_error_param(monkeypatch, repo, user_data):
    user = User(**user_data)

    def fail_commit():
        raise SQLAlchemyError("DB error")

    monkeypatch.setattr(repo.session, "commit", fail_commit)
    with pytest.raises(RuntimeError) as excinfo:
        repo.add(user)
    assert "Failed to add user" in str(excinfo.value)
