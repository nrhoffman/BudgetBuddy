import pytest
from datetime import datetime
from app.models.raw_provider_data import Cursor, Identity, RawProviderData

# ---------------------------
# Test Cursor
# ---------------------------

@pytest.mark.parametrize(
    "before, after",
    [
        (None, None),
        ("cur_123", "cur_456"),
    ]
)
def test_cursor_init(before, after):
    cursor = Cursor(before=before, after=after)
    assert cursor.before == before
    assert cursor.after == after

def test_cursor_repr_and_frozen():
    cursor = Cursor(before="b1", after="a1")
    repr_str = repr(cursor)
    assert "Cursor" in repr_str
    assert cursor.before == "b1"
    # test frozen behavior
    with pytest.raises(AttributeError):
        cursor.before = "new_value"


# ---------------------------
# Test Identity
# ---------------------------

@pytest.mark.parametrize(
    "user_id, item_id",
    [
        (None, None),
        ("user_1", "item_1"),
    ]
)
def test_identity_init(user_id, item_id):
    identity = Identity(user_id=user_id, item_id=item_id)
    assert identity.user_id == user_id
    assert identity.item_id == item_id

def test_identity_repr_and_frozen():
    identity = Identity(user_id="u1", item_id="i1")
    repr_str = repr(identity)
    assert "Identity" in repr_str
    with pytest.raises(AttributeError):
        identity.user_id = "new_user"


# ---------------------------
# Test RawProviderData
# ---------------------------

@pytest.mark.parametrize(
    "provider, endpoint, payload, identity, cursor, occurred_at",
    [
        ("plaid", "transactions/get", {"key": "value"}, None, None, None),
        (
            "plaid",
            "accounts/get",
            {"accounts": []},
            Identity(user_id="u1", item_id="i1"),
            Cursor(before="b1", after="a1"),
            datetime(2026, 2, 10, 12, 0)
        ),
    ]
)
def test_raw_provider_data_init(provider, endpoint, payload, identity, cursor, occurred_at):
    # Use defaults if None
    if identity is None:
        identity = Identity()
    if cursor is None:
        cursor = Cursor()

    raw_data = RawProviderData(
        provider=provider,
        endpoint=endpoint,
        payload=payload,
        identity=identity,
        cursor=cursor,
        occurred_at=occurred_at
    )

    assert raw_data.provider == provider
    assert raw_data.endpoint == endpoint
    assert raw_data.payload == payload
    assert raw_data.identity == identity
    assert raw_data.cursor == cursor
    assert raw_data.occurred_at == occurred_at


def test_raw_provider_data_repr_and_frozen():
    identity = Identity(user_id="u1", item_id="i1")
    cursor = Cursor(before="b1", after="a1")
    occurred_at = datetime(2026, 2, 10, 12, 0)

    raw_data = RawProviderData(
        provider="plaid",
        endpoint="test/endpoint",
        payload={"x": 1},
        identity=identity,
        cursor=cursor,
        occurred_at=occurred_at
    )

    repr_str = repr(raw_data)
    assert "RawProviderData" in repr_str
    assert raw_data.identity == identity
    # frozen test
    with pytest.raises(AttributeError):
        raw_data.provider = "new_provider"
