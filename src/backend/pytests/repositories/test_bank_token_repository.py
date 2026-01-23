import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base
from app.models.bank_item_token import BankItemToken
from app.repositories.bank_token_repository import BankTokenRepository


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
    return BankTokenRepository(db_session)


# -----------------------
# Parametrized test: save and fetch tokens
# -----------------------
@pytest.mark.parametrize(
    "user_id, provider, access_token, item_id",
    [
        ("user_001", "Plaid", "token_123", "item_abc"),
        ("user_002", "Chase", "token_456", "item_def"),
        ("user_003", "Venmo", "token_789", "item_ghi"),
    ]
)
def test_save_and_get_token_param(repo, user_id, provider, access_token, item_id):
    repo.save(user_id, provider, access_token, item_id)

    token = repo.get_by_user(user_id, provider)
    assert token is not None
    assert token.user_id == user_id
    assert token.provider == provider
    assert token.access_token == access_token
    assert token.item_id == item_id


# -----------------------
# Parametrized test: fetching non-existent tokens
# -----------------------
@pytest.mark.parametrize(
    "user_id, provider",
    [
        ("nonexistent_user", "Plaid"),
        ("user_999", "Chase"),
    ]
)
def test_get_nonexistent_token_param(repo, user_id, provider):
    token = repo.get_by_user(user_id, provider)
    assert token is None


# -----------------------
# Parametrized test: error handling during save
# -----------------------
@pytest.mark.parametrize(
    "user_id, provider, access_token, item_id",
    [
        ("user_004", "Plaid", "token_xyz", "item_999"),
        ("user_005", "Chase", "token_abc", "item_888"),
    ]
)
def test_save_invalid_session_param(monkeypatch, repo, user_id, provider, access_token, item_id):
    def fail_add(*args, **kwargs):
        raise SQLAlchemyError("DB error")

    monkeypatch.setattr(repo.session, "add", fail_add)
    with pytest.raises(RuntimeError) as excinfo:
        repo.save(user_id, provider, access_token, item_id)

    assert "Failed to save bank token" in str(excinfo.value)
