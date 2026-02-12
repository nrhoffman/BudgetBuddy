import pytest
from unittest.mock import MagicMock
from app.repositories.bank_repository import BankRepository
from app.models.exchange_token import ExchangeToken
from app.db.bank_item_token_orm import BankItemTokenORM
from app.db.bank_item_cursor_orm import BankItemCursorORM

# ---------------------------
# Fixture: Mocked SQLAlchemy session
# ---------------------------
@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def repo(mock_session):
    return BankRepository(mock_session)

# ---------------------------
# save_token
# ---------------------------
@pytest.mark.parametrize("existing_token", [None, MagicMock(spec=BankItemTokenORM)])
def test_save_token(repo, mock_session, existing_token):
    mock_session.scalar.return_value = existing_token
    token = ExchangeToken(
        public_token="access123",
        institution_id="inst1",
        institution_name="Bank A",
    )

    repo.save_token("user1", "plaid", "item123", token)

    if existing_token:
        assert existing_token.access_token == "access123"
        assert existing_token.item_id == "item123"
        assert existing_token.institution_name == "Bank A"
    else:
        # Check that add was called with a BankItemTokenORM instance
        assert mock_session.add.call_count == 1
        added_obj = mock_session.add.call_args[0][0]
        assert isinstance(added_obj, BankItemTokenORM)
        assert added_obj.access_token == "access123"
        assert added_obj.item_id == "item123"

# ---------------------------
# save_cursor
# ---------------------------
@pytest.mark.parametrize("existing_cursor", [None, MagicMock(spec=BankItemCursorORM)])
def test_save_cursor(repo, mock_session, existing_cursor):
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = existing_cursor
    repo.save_cursor("user1", "item123", "cursor456")

    if existing_cursor:
        assert existing_cursor.cursor == "cursor456"
        assert hasattr(existing_cursor, "updated_at")
    else:
        # Check that add was called with a BankItemCursorORM instance
        assert mock_session.add.call_count == 1
        added_obj = mock_session.add.call_args[0][0]
        assert isinstance(added_obj, BankItemCursorORM)
        assert added_obj.cursor == "cursor456"
        assert added_obj.user_id == "user1"
        assert added_obj.item_id == "item123"
