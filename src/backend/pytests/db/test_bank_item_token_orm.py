"""
Tests for the BankItemToken ORM model.

Validates creation, nullable fields, and timestamp defaults.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.bank_item_token_orm import BankItemToken


# -----------------------
# Fixture: in-memory SQLite
# -----------------------
@pytest.fixture
def db_session():
    """Provide a SQLAlchemy session using in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


# -----------------------
# Parametrized creation tests
# -----------------------
@pytest.mark.parametrize(
    (
        "user_id",
        "provider",
        "institution_id",
        "institution_name",
        "access_token",
        "item_id",
    ),
    [
        (
            "user_001",
            "plaid",
            "ins_001",
            "Chase",
            "token_abc",
            "item_001",
        ),
        (
            "user_002",
            "plaid",
            "ins_002",
            None,
            "token_xyz",
            "item_002",
        ),
    ],
)
def test_bank_item_token_creation(
    db_session,
    user_id,
    provider,
    institution_id,
    institution_name,
    access_token,
    item_id,
):
    """Ensure BankItemToken rows persist correctly."""
    token = BankItemToken(
        user_id=user_id,
        provider=provider,
        institution_id=institution_id,
        institution_name=institution_name,
        access_token=access_token,
        item_id=item_id,
    )

    db_session.add(token)
    db_session.commit()

    saved = (
        db_session.query(BankItemToken)
        .filter_by(user_id=user_id, item_id=item_id)
        .one()
    )

    assert saved.id is not None
    assert saved.user_id == user_id
    assert saved.provider == provider
    assert saved.institution_id == institution_id
    assert saved.institution_name == institution_name
    assert saved.access_token == access_token
    assert saved.item_id == item_id
    assert isinstance(saved.created_at, datetime)


# -----------------------
# Timestamp behavior
# -----------------------
def test_bank_item_token_created_at_timezone(db_session):
    """created_at should be set on insert (timezone-aware if supported)."""
    token = BankItemToken(
        user_id="user_010",
        provider="plaid",
        institution_id="ins_010",
        institution_name="Bank",
        access_token="token_123",
        item_id="item_010",
    )

    db_session.add(token)
    db_session.commit()

    saved = (
        db_session.query(BankItemToken)
        .filter_by(user_id="user_010", item_id="item_010")
        .one()
    )

    assert isinstance(saved.created_at, datetime)

    created_at_utc = (
        saved.created_at
        if saved.created_at.tzinfo is not None
        else saved.created_at.replace(tzinfo=timezone.utc)
    )

    now_utc = datetime.now(timezone.utc)

    assert created_at_utc <= now_utc
    assert created_at_utc >= now_utc - timedelta(seconds=5)
