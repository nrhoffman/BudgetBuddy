import pytest
from datetime import datetime, timezone
from app.models.bank_item_token import BankItemToken
from app.db.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# -----------------------
# Fixture: In-memory database
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
# Parametrize valid tokens
# -----------------------
@pytest.mark.parametrize(
    "user_id, provider, access_token, item_id",
    [
        ("user_001", "Plaid", "token_001", "item_001"),
        ("user_002", "Chase", "token_002", None),
        ("user_003", "WellsFargo", "token_003", "item_003"),
    ]
)
def test_bank_item_token_creation(db_session, user_id, provider, access_token, item_id):
    token = BankItemToken(
        user_id=user_id,
        provider=provider,
        access_token=access_token,
        item_id=item_id
    )
    db_session.add(token)
    db_session.commit()

    saved_token = db_session.query(BankItemToken).filter_by(user_id=user_id).first()
    assert saved_token is not None
    assert isinstance(saved_token.id, str)
    assert saved_token.user_id == user_id
    assert saved_token.provider == provider
    assert saved_token.access_token == access_token
    assert saved_token.item_id == item_id

    created = saved_token.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    assert (datetime.now(timezone.utc) - created).total_seconds() < 5

# -----------------------
# Optional item_id specifically
# -----------------------
def test_bank_item_token_optional_item_id(db_session):
    token = BankItemToken(
        user_id="user_optional",
        provider="BankX",
        access_token="token_optional",
        item_id=None
    )
    db_session.add(token)
    db_session.commit()
    saved_token = db_session.query(BankItemToken).filter_by(user_id="user_optional").first()
    assert saved_token.item_id is None
