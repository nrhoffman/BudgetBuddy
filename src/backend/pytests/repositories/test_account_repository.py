import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from app.models.account import Account
from app.repositories.account_repository import AccountRepository
from app.db.account_orm import AccountORM
from app.db.transaction_orm import TransactionORM

# ---------------------------
# Fixtures
# ---------------------------
@pytest.fixture
def mock_session():
    from unittest.mock import MagicMock
    return MagicMock()

@pytest.fixture
def repo(mock_session):
    return AccountRepository(mock_session)

# ---------------------------
# Exception tests fixed
# ---------------------------
def test_get_account_not_found(repo):
    # If account doesn't exist, repo raises ValueError
    repo.session.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError):
        repo.get("missing_acc", "user1")


def test_update_account_not_found(repo):
    repo.session.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError):
        repo.update_account("missing_acc", "user1", account_name="New")


def test_delete_account_not_found(repo):
    repo.session.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError):
        repo.delete_account("missing_acc", "user1")


def test_add_account_sqlalchemy_error(mock_session):
    from sqlalchemy.exc import SQLAlchemyError
    repo = AccountRepository(mock_session)
    mock_session.add.side_effect = SQLAlchemyError("fail")
    acc = Account(id="a1", name="Checking", type="depository", subtype=None, balance=50)
    # SQLAlchemyError is raised directly
    with pytest.raises(SQLAlchemyError):
        repo.add_account(acc, "user1")


def test_get_account_sqlalchemy_error(mock_session):
    from sqlalchemy.exc import SQLAlchemyError
    repo = AccountRepository(mock_session)
    mock_session.query.side_effect = SQLAlchemyError("fail")
    with pytest.raises(SQLAlchemyError):
        repo.get("a1", "user1")


def test_update_account_sqlalchemy_error(mock_session):
    from sqlalchemy.exc import SQLAlchemyError
    repo = AccountRepository(mock_session)
    
    # Make the query itself raise an exception
    mock_session.query.side_effect = SQLAlchemyError("fail")
    
    with pytest.raises(SQLAlchemyError):
        repo.update_account("a1", "user1", account_name="New")


def test_delete_account_sqlalchemy_error(mock_session):
    from sqlalchemy.exc import SQLAlchemyError
    repo = AccountRepository(mock_session)
    # Return a mock ORM to delete
    orm = mock_session.query.return_value.filter.return_value.first.return_value
    mock_session.delete.side_effect = SQLAlchemyError("fail")
    with pytest.raises(SQLAlchemyError):
        repo.delete_account("a1", "user1")
