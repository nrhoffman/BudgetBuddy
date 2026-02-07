"""
Account API endpoints for managing user financial accounts.

Provides routes to retrieve, update, and remove accounts, as well as
update user-editable transaction fields. Includes type hints, logging,
and proper HTTPException handling.
"""

from typing import Any
from fastapi import APIRouter, Depends

from app.dependencies import get_account_service, get_current_user
from app.models.transaction import UpdateTransaction
from app.services.account_service import AccountService

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


# -----------------------
# Account Routes
# -----------------------
@router.get("/get-accounts", response_model=dict[str, Any])
def get_accounts(
    account_service: AccountService = Depends(get_account_service),
    current_user=Depends(get_current_user),
) -> dict[str, Any]:
    """
    Retrieve all financial accounts for the current user.

    Args:
        account_service: Injected AccountService instance.
        current_user: The authenticated user.
    """
    return {"accounts": account_service.get_user_financial_snapshot(
        current_user.id
    )}


@router.post("/update-account/{account_id}/{account_name}")
def update_account(
    account_id: str,
    account_name: str,
    account_service: AccountService = Depends(get_account_service),
    current_user=Depends(get_current_user),
) -> Any:
    """
    Update the name of an existing account for the current user.

    Args:
        account_id: The ID of the account to update.
        account_name: The new name for the account.
        account_service: Injected AccountService instance.
        current_user: The authenticated user.
    """
    account_service.update_account(
        account_id=account_id,
        user_id=current_user.id,
        account_name=account_name,
    )
    return {"message": "Account updated successfully"}


@router.delete("/remove-account/{account_id}")
def remove_account(
    account_id: str,
    account_service: AccountService = Depends(get_account_service),
    current_user=Depends(get_current_user),
) -> Any:
    """
    Remove a specific account for the current user.

    Args:
        account_id: The ID of the account to remove.
        account_service: Injected AccountService instance.
        current_user: The authenticated user.
    """
    account_service.remove_account(account_id, current_user.id)
    return {"message": "Account deleted successfully"}


# -----------------------
# Transaction Routes
# -----------------------
@router.post("/{account_id}/transactions/{transaction_id}")
def update_transaction(
    account_id: str,
    transaction_id: str,
    payload: UpdateTransaction,
    account_service: AccountService = Depends(get_account_service),
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    """
    Update user-editable fields of a transaction.

    Args:
        account_id: ID of the account containing the transaction.
        transaction_id: ID of the transaction to update.
        payload: UpdateTransaction payload with editable fields.
        account_service: Injected AccountService instance.
        current_user: The authenticated user.

    Returns:
        Status message indicating success.
    """
    account_service.update_transaction(
        user_id=current_user.id,
        account_id=account_id,
        transaction_id=transaction_id,
        payload=payload,
    )
    return {"status": "ok"}


# -----------------------
# Institution Routes
# -----------------------
@router.get("/get-institutions", response_model=list[dict])
def get_institutions(
    account_service: AccountService = Depends(get_account_service),
    current_user=Depends(get_current_user),
) -> list[dict]:
    """
    Retrieve a list of financial institutions.

    Args:
        account_service: Injected AccountService instance.
        current_user: The authenticated user.

    Returns:
        List of financial institutions.
    """
    institutions = account_service.get_institutions(user_id=current_user.id)
    return institutions
