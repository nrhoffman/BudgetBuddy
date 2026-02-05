import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime

from app.repositories.transaction_repository import TransactionRepository
from app.models.transaction import Transaction
from sqlalchemy.exc import SQLAlchemyError

# ---------------------------
# Fixtures
# ---------------------------
@pytest.fixture
def session():
    return MagicMock()

@pytest.fixture
def repo(session):
    return TransactionRepository(session)

@pytest.fixture
def sample_txn():
    return Transaction(
        transaction_id="txn_001",
        account_id="acc_001",
        amount=Decimal("100.0"),
        balance_after=Decimal("500.0"),
        name="Sample Payment",
        merchant_name="Merchant",
        category_primary="EXPENSE",
        category_detailed="Food",
        category_confidence_level="0.9",
        pending=False,
        iso_currency_code="USD",
        unofficial_currency_code=None,
        date=datetime(2026, 2, 3)
    )

@pytest.fixture
def sample_txn2():
    return Transaction(
        transaction_id="txn_002",
        account_id="acc_002",
        amount=Decimal("-50.0"),
        balance_after=Decimal("450.0"),
        name="Refund",
        merchant_name="Merchant2",
        category_primary="INCOME",
        category_detailed="Refunds",
        category_confidence_level="0.8",
        pending=True,
        iso_currency_code="USD",
        unofficial_currency_code=None,
        date=datetime(2026, 2, 2)
    )

# ---------------------------
# get_by_ids
# ---------------------------
@pytest.mark.parametrize(
    "transaction_ids, orm_results, expected_count, raise_exc",
    [
        (["txn1", "txn2"], [MagicMock(), MagicMock()], 2, False),
        ([], [], 0, False),
        (["txn1"], [], 0, False),
        (["txn1"], None, 0, True),
    ]
)
def test_get_by_ids(repo, session, transaction_ids, orm_results, expected_count, raise_exc):
    session.query.return_value.filter.return_value.all.return_value = orm_results

    if raise_exc:
        session.query.side_effect = SQLAlchemyError("fail")
        with pytest.raises(RuntimeError):
            repo.get_by_ids(transaction_ids)
    else:
        with patch("app.repositories.transaction_repository.orm_to_domain_transaction",
                   side_effect=lambda orm: orm):
            result = repo.get_by_ids(transaction_ids)
            assert len(result) == expected_count

# ---------------------------
# bulk_upsert
# ---------------------------
@pytest.mark.parametrize(
    "txns, execute_rowcount, expected_return, raise_exc",
    [
        ([], 0, 0, False),                 # empty list
        ("one_txn", 1, 1, False),          # single transaction
        ("two_txns", 2, 2, False),         # multiple transactions
        ("one_txn", None, 0, False),       # rowcount None
        ("one_txn", None, None, True),     # exception
    ]
)
def test_bulk_upsert(repo, session, sample_txn, sample_txn2, txns, execute_rowcount, expected_return, raise_exc):
    # Prepare proper transaction list
    if txns == "one_txn":
        tx_list = [sample_txn]
    elif txns == "two_txns":
        tx_list = [sample_txn, sample_txn2]
    else:
        tx_list = []

    mock_result = MagicMock()
    mock_result.rowcount = execute_rowcount

    if raise_exc:
        session.execute.side_effect = SQLAlchemyError("fail")
        with pytest.raises(RuntimeError):
            repo.bulk_upsert("user1", tx_list)
    else:
        session.execute.return_value = mock_result
        count = repo.bulk_upsert("user1", tx_list)
        # If rowcount is None, repo should default to 0
        expected_count = expected_return if expected_return is not None else 0
        assert count == expected_count

# ---------------------------
# delete_by_ids
# ---------------------------
@pytest.mark.parametrize(
    "transaction_ids, deleted_count, expected_return, raise_exc",
    [
        ([], 0, 0, False),                 # empty list
        (["txn1"], 1, 1, False),           # normal
        (["txn1"], None, None, True),      # exception
    ]
)
def test_delete_by_ids(repo, session, transaction_ids, deleted_count, expected_return, raise_exc):
    if raise_exc:
        session.query.return_value.join.return_value.filter.return_value.delete.side_effect = SQLAlchemyError("fail")
        with pytest.raises(RuntimeError):
            repo.delete_by_ids("user1", transaction_ids)
    else:
        session.query.return_value.join.return_value.filter.return_value.delete.return_value = deleted_count
        count = repo.delete_by_ids("user1", transaction_ids)
        expected_count = expected_return if expected_return is not None else deleted_count
        assert count == expected_count
