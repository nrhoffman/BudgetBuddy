import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import MagicMock

from app.services.account_service import AccountService
from app.models.account import Account, UpdateAccount
from app.models.transaction import Transaction, UpdateTransaction
from app.exceptions import DatabaseError, NotFoundError, ValidationError


# ---------------------------
# Fixtures
# ---------------------------

@pytest.fixture
def account_repo_mock(mocker):
    return mocker.Mock()

@pytest.fixture
def bank_repo_mock(mocker):
    return mocker.Mock()

@pytest.fixture
def txn_repo_mock(mocker):
    return mocker.Mock()

@pytest.fixture
def account_service(account_repo_mock, bank_repo_mock, txn_repo_mock):
    return AccountService(
        account_repo=account_repo_mock,
        bank_repo=bank_repo_mock,
        txn_repo=txn_repo_mock,
    )

@pytest.fixture
def sample_account():
    return Account(
        id="acc1",
        name="Checking",
        balance=Decimal("100.0"),
        initial_import_completed_at=datetime(2026, 1, 1),
        transactions=[],
        type="depository",
        subtype="checking",
    )

@pytest.fixture
def update_payload():
    return UpdateTransaction(amount=Decimal("75.0"))


# ---------------------------
# create_account
# ---------------------------

@pytest.mark.parametrize(
    "side_effect,expected_exception",
    [
        (None, None),
        (SQLAlchemyError("fail"), DatabaseError),
    ],
)
def test_create_account(account_service, account_repo_mock, sample_account, side_effect, expected_exception):
    account_repo_mock.add_account.side_effect = side_effect

    if expected_exception:
        with pytest.raises(expected_exception):
            account_service.create_account(sample_account, "user1")
    else:
        result = account_service.create_account(sample_account, "user1")
        assert result == {
            "account_id": sample_account.id,
            "message": "Account created",
        }


# ---------------------------
# get_account
# ---------------------------

@pytest.mark.parametrize(
    "repo_return,side_effect,expected_exception",
    [
        ("found", None, None),
        (None, None, NotFoundError),
        (None, Exception("fail"), DatabaseError),
    ],
)
def test_get_account(account_service, account_repo_mock, sample_account, repo_return, side_effect, expected_exception):
    account_repo_mock.get.return_value = sample_account if repo_return == "found" else None
    account_repo_mock.get.side_effect = side_effect

    if expected_exception:
        with pytest.raises(expected_exception):
            account_service.get_account("acc1", "user1")
    else:
        result = account_service.get_account("acc1", "user1")
        assert result == sample_account


# ---------------------------
# update_account
# ---------------------------


@pytest.mark.parametrize(
    "payload,balance,side_effect,expected_exception",
    [
        (UpdateAccount(account_name="New Name"), None, None, None),
        (UpdateAccount(apr=3.5), None, None, None),
        (None, 200.0, None, None),
        (UpdateAccount(account_name="New Name", apr=3.5), 200.0, None, None),
        (UpdateAccount(), None, None, ValidationError),
        (UpdateAccount(account_name="Name"), None, ValueError("not found"), NotFoundError),
        (UpdateAccount(account_name="Name"), None, Exception("fail"), DatabaseError),
    ],
)
def test_update_account(
    account_service,
    account_repo_mock,
    payload,
    balance,
    side_effect,
    expected_exception,
):
    account_repo_mock.update_account.side_effect = side_effect

    if expected_exception:
        with pytest.raises(expected_exception):
            account_service.update_account(
                account_id="acc1",
                user_id="user1",
                payload=payload,
                balance=balance,
            )
    else:
        result = account_service.update_account(
            account_id="acc1",
            user_id="user1",
            payload=payload,
            balance=balance,
        )
        assert result is None
        account_repo_mock.update_account.assert_called_once()


# ---------------------------
# remove_account
# ---------------------------

@pytest.mark.parametrize(
    "side_effect,expected_exception",
    [
        (None, None),
        (ValueError("not found"), NotFoundError),
        (Exception("fail"), DatabaseError),
    ],
)
def test_remove_account(account_service, account_repo_mock, side_effect, expected_exception):
    account_repo_mock.delete_account.side_effect = side_effect

    if expected_exception:
        with pytest.raises(expected_exception):
            account_service.remove_account("acc1", "user1")
    else:
        assert account_service.remove_account("acc1", "user1") is None


# ---------------------------
# update_transaction
# ---------------------------

@pytest.mark.parametrize(
    "txns_return,account_id,apply_side_effect,expected_exception",
    [
        ([], "acc1", None, NotFoundError),
        ([Transaction(transaction_id="tx1", account_id="wrong", date=datetime.now(), amount=Decimal(1))],
         "acc1", None, DatabaseError),
        ([Transaction(transaction_id="tx1", account_id="acc1", date=datetime.now(), amount=Decimal(1))],
         "acc1", None, None),
        ([Transaction(transaction_id="tx1", account_id="acc1", date=datetime.now(), amount=Decimal(1))],
         "acc1", Exception("fail"), DatabaseError),
    ],
)
def test_update_transaction(
    account_service,
    txn_repo_mock,
    update_payload,
    txns_return,
    account_id,
    apply_side_effect,
    expected_exception,
):
    txn_repo_mock.get_by_ids.return_value = txns_return
    account_service.apply_transaction_changes = MagicMock(side_effect=apply_side_effect)

    if expected_exception:
        with pytest.raises(expected_exception):
            account_service.update_transaction("user1", account_id, "tx1", update_payload)
    else:
        account_service.update_transaction("user1", account_id, "tx1", update_payload)
        account_service.apply_transaction_changes.assert_called_once()


# ---------------------------
# apply_transaction_changes
# ---------------------------

@pytest.mark.parametrize(
    "added,modified,removed,expect_non_empty_upsert",
    [
        ([Transaction(transaction_id="tx1", account_id="acc1", date=datetime.now(), amount=Decimal(1))], [], [], True),
        ([], [Transaction(transaction_id="tx1", account_id="acc1", date=datetime.now(), amount=Decimal(1))], [], True),
        ([], [], ["tx1"], False),
        ([], [], [], False),
    ],
)
def test_apply_transaction_changes(account_service, added, modified, removed, expect_non_empty_upsert):
    account_service._remove_transactions = MagicMock()
    account_service._upsert_transactions = MagicMock()
    account_service._rebalance_accounts = MagicMock()
    account_service.find_earliest_dates = MagicMock(return_value={"acc1": {}})

    account_service.apply_transaction_changes(
        user_id="user1",
        added=added,
        modified=modified,
        removed=removed,
    )

    account_service._remove_transactions.assert_called_once_with("user1", removed)

    upsert_payloads = [call.args[0] for call in account_service._upsert_transactions.call_args_list]

    if expect_non_empty_upsert:
        assert any(upsert_payloads)
    else:
        assert all(not payload for payload in upsert_payloads)

    account_service._rebalance_accounts.assert_called_once()


# ---------------------------
# find_earliest_dates
# ---------------------------

# ---------------------------
# find_earliest_dates
# ---------------------------

def test_find_earliest_dates_no_import_completed(account_service, account_repo_mock):
    acc = Account(
        id="acc1",
        name="Checking",
        balance=Decimal("100"),
        initial_import_completed_at=None,
        transactions=[],
        type="depository",
        subtype="checking",
    )
    account_repo_mock.get.return_value = acc
    account_service.txn_repo.get_by_ids.return_value = []

    txn1 = Transaction(
        transaction_id="tx1",
        account_id="acc1",
        date=datetime(2026, 1, 1),
        amount=Decimal("10"),
    )
    txn2 = Transaction(
        transaction_id="tx2",
        account_id="acc1",
        date=datetime(2026, 2, 1),
        amount=Decimal("20"),
    )

    boundaries = account_service.find_earliest_dates("user1", [txn1, txn2], [], [])

    assert boundaries["acc1"]["latest_before_import"] is None
    assert boundaries["acc1"]["earliest_after_import"] == txn1.date


def test_find_earliest_dates_with_import_date(account_service, account_repo_mock):
    acc = Account(
        id="acc1",
        name="Checking",
        balance=Decimal("100"),
        initial_import_completed_at=datetime(2026, 1, 15),
        transactions=[],
        type="depository",
        subtype="checking",
    )
    account_repo_mock.get.return_value = acc
    account_service.txn_repo.get_by_ids.return_value = []

    before = Transaction(
        transaction_id="tx1",
        account_id="acc1",
        date=datetime(2026, 1, 1),
        amount=Decimal("10"),
    )
    after = Transaction(
        transaction_id="tx2",
        account_id="acc1",
        date=datetime(2026, 2, 1),
        amount=Decimal("20"),
    )

    boundaries = account_service.find_earliest_dates("user1", [before, after], [], [])

    assert boundaries["acc1"]["latest_before_import"] == before.date
    assert boundaries["acc1"]["earliest_after_import"] == after.date


# ---------------------------
# get_user_financial_snapshot
# ---------------------------

@pytest.mark.parametrize(
    "side_effect,expected_exception,result_value",
    [
        (None, None, ["account1"]),
        (SQLAlchemyError("fail"), DatabaseError, None),
    ],
)
def test_get_user_financial_snapshot(account_service, account_repo_mock, side_effect, expected_exception, result_value):
    account_repo_mock.get_all_accounts_with_transactions.side_effect = side_effect
    if side_effect is None:
        account_repo_mock.get_all_accounts_with_transactions.return_value = result_value

    if expected_exception:
        with pytest.raises(expected_exception):
            account_service.get_user_financial_snapshot("user1")
    else:
        assert account_service.get_user_financial_snapshot("user1") == result_value
