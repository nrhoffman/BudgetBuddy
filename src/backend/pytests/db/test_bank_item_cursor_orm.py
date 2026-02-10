"""
Tests for the BankItemCursorORM ORM model.

Validates creation, nullable cursor handling, and default timestamps.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.bank_item_cursor_orm import BankItemCursorORM


# -----------------------
# Fixture: in-memory SQLite
# -----------------------
@pytest.fixture
def db_session():
    """Provide a SQLAlchemy session using in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    BankItemCursorORM.__table__.create(engine)
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
        "item_id",
        "cursor",
    ),
    [
        ("user_001", "item_001", "cursor_abc"),
        ("user_002", "item_002", None),
        ("user_003", "item_003", "cursor_xyz"),
    ],
)
def test_bank_item_cursor_creation(
    db_session,
    user_id,
    item_id,
    cursor,
):
    """Ensure BankItemCursorORM rows persist correctly."""
    bank_cursor = BankItemCursorORM(
        user_id=user_id,
        item_id=item_id,
        cursor=cursor,
    )

    db_session.add(bank_cursor)
    db_session.commit()

    saved = (
        db_session.query(BankItemCursorORM)
        .filter_by(user_id=user_id, item_id=item_id)
        .one()
    )

    assert saved.id is not None
    assert saved.user_id == user_id
    assert saved.item_id == item_id
    assert saved.cursor == cursor
    assert isinstance(saved.updated_at, datetime)


# -----------------------
# Timestamp behavior
# -----------------------
def test_bank_item_cursor_updated_at_timezone(db_session):
    """updated_at should be set on insert (timezone-aware if supported)."""
    bank_cursor = BankItemCursorORM(
        user_id="user_010",
        item_id="item_010",
        cursor="cursor_val",
    )

    db_session.add(bank_cursor)
    db_session.commit()

    saved = (
        db_session.query(BankItemCursorORM)
        .filter_by(user_id="user_010", item_id="item_010")
        .one()
    )

    # Assert it exists
    assert isinstance(saved.updated_at, datetime)

    # Normalize to UTC for comparison
    updated_at_utc = (
        saved.updated_at
        if saved.updated_at.tzinfo is not None
        else saved.updated_at.replace(tzinfo=timezone.utc)
    )

    now_utc = datetime.now(timezone.utc)

    # Check that it was created in the past but very recently
    assert updated_at_utc <= now_utc
    assert updated_at_utc >= now_utc - timedelta(seconds=5)
