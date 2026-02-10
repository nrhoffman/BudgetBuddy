import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock

from app.models.raw_provider_data import RawProviderData, Identity, Cursor
from app.repositories.raw_provider_repository import RawProviderRepository

# ---------------------------
# Fixtures
# ---------------------------

@pytest.fixture
def mock_session():
    """Return a mock SQLAlchemy session."""
    return MagicMock()

@pytest.fixture
def sample_event():
    """Return a sample RawProviderData event."""
    return RawProviderData(
        provider="plaid",
        endpoint="transactions/get",
        payload={"amount": Decimal("12.34"), "date": date(2026, 2, 10)},
        identity=Identity(user_id="user_1", item_id="item_1"),
        cursor=Cursor(before="cur_0", after="cur_1"),
        occurred_at=datetime(2026, 2, 10, 12, 0)
    )

# ---------------------------
# Test initialization
# ---------------------------

def test_repository_init(mock_session):
    repo = RawProviderRepository(mock_session)
    assert repo.session == mock_session

# ---------------------------
# Test save method
# ---------------------------

def test_save_adds_to_session(mock_session, sample_event):
    repo = RawProviderRepository(mock_session)
    repo.save(sample_event)
    # Ensure session.add was called once
    assert mock_session.add.called
    added_obj = mock_session.add.call_args[0][0]
    # Check ORM mapping
    assert added_obj.provider == sample_event.provider
    assert added_obj.endpoint == sample_event.endpoint
    assert added_obj.user_id == sample_event.identity.user_id
    assert added_obj.item_id == sample_event.identity.item_id
    assert added_obj.cursor_before == sample_event.cursor.before
    assert added_obj.cursor_after == sample_event.cursor.after
    # payload should be json_safe converted
    assert added_obj.payload == {
        "amount": 12.34,
        "date": "2026-02-10"
    }
    assert added_obj.fetched_at == sample_event.occurred_at

def test_save_handles_missing_identity_and_cursor(mock_session):
    repo = RawProviderRepository(mock_session)
    event = RawProviderData(
        provider="plaid",
        endpoint="accounts/get",
        payload={"accounts": []},
        identity=None,
        cursor=None,
        occurred_at=None
    )
    repo.save(event)
    added_obj = mock_session.add.call_args[0][0]
    assert added_obj.user_id is None
    assert added_obj.item_id is None
    assert added_obj.cursor_before is None
    assert added_obj.cursor_after is None
    assert added_obj.fetched_at is None

# ---------------------------
# Test json_safe
# ---------------------------

@pytest.mark.parametrize(
    "input_value, expected",
    [
        ({"a": 1, "b": Decimal("2.5")}, {"a": 1, "b": 2.5}),
        ([Decimal("1.1"), 2, 3], [1.1, 2, 3]),
        (datetime(2026, 2, 10, 12, 0), "2026-02-10T12:00:00"),
        (date(2026, 2, 10), "2026-02-10"),
        ("string", "string"),
        (42, 42),
        ([{"nested": Decimal("3.5"), "dt": date(2026,2,10)}],
         [{"nested": 3.5, "dt": "2026-02-10"}])
    ]
)
def test_json_safe_variants(mock_session, input_value, expected):
    repo = RawProviderRepository(mock_session)
    result = repo.json_safe(input_value)
    assert result == expected
