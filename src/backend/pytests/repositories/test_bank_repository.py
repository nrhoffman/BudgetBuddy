import pytest
from unittest.mock import MagicMock
from sqlalchemy.exc import SQLAlchemyError
from app.repositories.bank_repository import BankRepository
from app.models.exchange_token import ExchangeToken
from app.db.bank_item_token_orm import BankItemToken
from app.db.bank_item_cursor_orm import BankItemCursor


# ---------------------------
# Fixture: Mocked SQLAlchemy session
# ---------------------------
@pytest.fixture
def mock_session():
    return MagicMock()


# ---------------------------
# Tests for save_token
# ---------------------------
@pytest.mark.parametrize("existing_token", [None, MagicMock(spec=BankItemToken)])
def test_save_token(mock_session, existing_token):
    repo = BankRepository(mock_session)
    mock_session.scalar.return_value = existing_token

    exchange_token = ExchangeToken(
        public_token="access123",
        institution_id="inst1",
        institution_name="Bank A",
    )

    repo.save_token("user1", "plaid", "item123", exchange_token)

    if existing_token:
        assert existing_token.access_token == "access123"
        assert existing_token.item_id == "item123"
        assert existing_token.institution_name == "Bank A"
    else:
        mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_save_token_exception(mock_session):
    repo = BankRepository(mock_session)
    mock_session.scalar.side_effect = SQLAlchemyError("fail")
    exchange_token = ExchangeToken(
        public_token="token",
        institution_id="inst1",
        institution_name="Bank A",
    )
    with pytest.raises(RuntimeError):
        repo.save_token("user", "prov", "item", exchange_token)
    mock_session.rollback.assert_called_once()


# ---------------------------
# Tests for get_by_user
# ---------------------------
@pytest.mark.parametrize("token_in_db, expected_return", [(MagicMock(spec=BankItemToken), True), (None, False)])
def test_get_by_user(mock_session, token_in_db, expected_return):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = token_in_db

    result = repo.get_by_user("user1", "inst1")
    assert (result is not None) == expected_return


def test_get_by_user_exception(mock_session):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.side_effect = SQLAlchemyError("fail")
    with pytest.raises(RuntimeError):
        repo.get_by_user("user1", "inst1")


# ---------------------------
# Tests for get_token_by_item_id
# ---------------------------
@pytest.mark.parametrize("token_in_db, expected_return", [(MagicMock(spec=BankItemToken), True), (None, False)])
def test_get_token_by_item_id(mock_session, token_in_db, expected_return):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = token_in_db

    result = repo.get_token_by_item_id("item1")
    assert (result is not None) == expected_return


def test_get_token_by_item_id_exception(mock_session):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.side_effect = SQLAlchemyError("fail")
    with pytest.raises(RuntimeError):
        repo.get_token_by_item_id("item1")


# ---------------------------
# Tests for save_cursor
# ---------------------------
@pytest.mark.parametrize("existing_cursor", [None, MagicMock(spec=BankItemCursor)])
def test_save_cursor(mock_session, existing_cursor):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = existing_cursor

    repo.save_cursor("user1", "item123", "cursor456")

    if existing_cursor:
        assert existing_cursor.cursor == "cursor456"
        assert existing_cursor.updated_at is not None
    else:
        mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_save_cursor_exception(mock_session):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.side_effect = SQLAlchemyError("fail")
    with pytest.raises(RuntimeError):
        repo.save_cursor("user1", "item1", "cursor")


# ---------------------------
# Tests for get_cursor_by_item_id
# ---------------------------
@pytest.mark.parametrize("cursor_in_db, expected_return", [(MagicMock(spec=BankItemCursor), True), (None, False)])
def test_get_cursor_by_item_id(mock_session, cursor_in_db, expected_return):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = cursor_in_db

    result = repo.get_cursor_by_item_id("item1")
    assert (result is not None) == expected_return


def test_get_cursor_by_item_id_exception(mock_session):
    repo = BankRepository(mock_session)
    mock_session.query.return_value.filter_by.return_value.one_or_none.side_effect = SQLAlchemyError("fail")
    with pytest.raises(RuntimeError):
        repo.get_cursor_by_item_id("item1")


# ---------------------------
# Tests for get_institutions
# ---------------------------
def test_get_institutions_success(mock_session):
    repo = BankRepository(mock_session)

    # Mock the execute return value
    mock_inst1 = MagicMock(institution_id="inst1", institution_name="Bank A")
    mock_inst2 = MagicMock(institution_id="inst2", institution_name="Bank B")
    mock_session.execute.return_value.all.return_value = [mock_inst1, mock_inst2]

    result = repo.get_institutions("user123")
    assert result == [
        {"institution_id": "inst1", "institution_name": "Bank A"},
        {"institution_id": "inst2", "institution_name": "Bank B"},
    ]

    # Ensure the session.execute was called
    assert mock_session.execute.called


def test_get_institutions_empty(mock_session):
    repo = BankRepository(mock_session)
    mock_session.execute.return_value.all.return_value = []

    result = repo.get_institutions("user123")
    assert result == []
