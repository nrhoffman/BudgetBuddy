import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError

from app.repositories.bank_repository import BankRepository
from app.db.bank_item_token_orm import BankItemToken
from app.db.bank_item_cursor_orm import BankItemCursor
from app.models.exchange_token import ExchangeToken


# ---------------------------
# Fixture: Mocked SQLAlchemy session
# ---------------------------
@pytest.fixture
def mock_session():
    return MagicMock()


# ---------------------------
# Parametrize save_token scenarios
# ---------------------------
@pytest.mark.parametrize(
    "existing_token",
    [None, MagicMock(spec=BankItemToken)]
)
def test_save_token(mock_session, existing_token):
    repo = BankRepository(mock_session)
    
    # Patch session.scalar to return existing_token
    mock_session.scalar.return_value = existing_token

    user_id = "user1"
    provider = "plaid"
    institution_id = "inst1"
    institution_name = "Bank A"
    access_token = "access123"
    item_id = "item123"

    exchange_token =ExchangeToken(
        public_token=access_token,
        institution_id=institution_id,
        institution_name=institution_name,
    )

    repo.save_token(user_id, provider, item_id, exchange_token)

    if existing_token:
        # Should update existing token
        assert existing_token.access_token == access_token
        assert existing_token.item_id == item_id
        assert existing_token.institution_name == institution_name
    else:
        # Should add a new token
        mock_session.add.assert_called_once()
    
    # Should commit in both cases
    mock_session.commit.assert_called_once()


# ---------------------------
# Parametrize save_token exception
# ---------------------------
def test_save_token_exception(mock_session):
    repo = BankRepository(mock_session)
    mock_session.scalar.side_effect = SQLAlchemyError("fail")
    exchange_token =ExchangeToken(
        public_token="token",
        institution_id="inst1",
        institution_name="Bank A",
    )
    with pytest.raises(RuntimeError):
        repo.save_token("user", "prov", "item", exchange_token)
    mock_session.rollback.assert_called_once()


# ---------------------------
# Parametrize get_by_user scenarios
# ---------------------------
@pytest.mark.parametrize(
    "token_in_db, expected_return",
    [
        (MagicMock(spec=BankItemToken), True),
        (None, False),
    ]
)
def test_get_by_user(mock_session, token_in_db, expected_return):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = token_in_db

    result = repo.get_by_user("user1", "inst1")

    assert (result is not None) == expected_return


# ---------------------------
# Parametrize get_by_user exception
# ---------------------------
def test_get_by_user_exception(mock_session):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.side_effect = SQLAlchemyError("fail")
    with pytest.raises(RuntimeError):
        repo.get_by_user("user1", "inst1")


# ---------------------------
# Parametrize get_token_by_item_id scenarios
# ---------------------------
@pytest.mark.parametrize(
    "token_in_db, expected_return",
    [
        (MagicMock(spec=BankItemToken), True),
        (None, False),
    ]
)
def test_get_token_by_item_id(mock_session, token_in_db, expected_return):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = token_in_db

    result = repo.get_token_by_item_id("item1")

    assert (result is not None) == expected_return


# ---------------------------
# Parametrize get_token_by_item_id exception
# ---------------------------
def test_get_token_by_item_id_exception(mock_session):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.side_effect = SQLAlchemyError("fail")
    with pytest.raises(RuntimeError):
        repo.get_token_by_item_id("item1")


# ---------------------------
# Parametrize save_cursor scenarios
# ---------------------------
@pytest.mark.parametrize(
    "existing_cursor",
    [None, MagicMock(spec=BankItemCursor)]
)
def test_save_cursor(mock_session, existing_cursor):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = existing_cursor

    user_id = "user1"
    item_id = "item123"
    cursor_value = "cursor456"

    repo.save_cursor(user_id, item_id, cursor_value)

    if existing_cursor:
        # Should update existing cursor
        assert existing_cursor.cursor == cursor_value
        assert existing_cursor.updated_at is not None
    else:
        # Should add a new cursor
        mock_session.add.assert_called_once()
    
    mock_session.commit.assert_called_once()


# ---------------------------
# Parametrize save_cursor exception
# ---------------------------
def test_save_cursor_exception(mock_session):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.side_effect = SQLAlchemyError("fail")
    with pytest.raises(RuntimeError):
        repo.save_cursor("user1", "item1", "cursor")


# ---------------------------
# Parametrize get_cursor_by_item_id scenarios
# ---------------------------
@pytest.mark.parametrize(
    "cursor_in_db, expected_return",
    [
        (MagicMock(spec=BankItemCursor), True),
        (None, False),
    ]
)
def test_get_cursor_by_item_id(mock_session, cursor_in_db, expected_return):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = cursor_in_db

    result = repo.get_cursor_by_item_id("item1")
    assert (result is not None) == expected_return


# ---------------------------
# Parametrize get_cursor_by_item_id exception
# ---------------------------
def test_get_cursor_by_item_id_exception(mock_session):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.side_effect = SQLAlchemyError("fail")
    with pytest.raises(RuntimeError):
        repo.get_cursor_by_item_id("item1")
