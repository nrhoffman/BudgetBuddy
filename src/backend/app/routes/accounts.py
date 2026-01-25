"""
Account API endpoints for managing user financial accounts.
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_account_service, get_current_user
from app.services.account_service import AccountService

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("/get-accounts")
def get_accounts(
    account_service: AccountService = Depends(get_account_service),
    current_user=Depends(get_current_user),
):
    """
    Retrieve all financial accounts for the current user.

    Args:
        budget_service: Injected BudgetService instance.
        current_user: The authenticated user.

    Returns:
        Dict containing the list of accounts.
    """
    accounts = account_service.get_user_financial_snapshot(current_user.id)
    return {"accounts": accounts}


@router.post("/update-account/{account_id}/{account_name}")
def update_account(
    account_id: str,
    account_name: str,
    budget_service: AccountService = Depends(get_account_service),
    current_user=Depends(get_current_user),
):
    """
    Update the name of an existing account for the current user.

    Args:
        account_id: The ID of the account to update.
        account_name: The new name for the account.
        budget_service: Injected BudgetService instance.
        current_user: The currently authenticated user.

    Returns:
        Result of the account update operation.
    """
    return budget_service.update_account(
        account_id = account_id,
        user_id = current_user.id,
        account_name = account_name)


@router.delete("/remove-account/{account_id}")
def remove_account(
    account_id: str,
    budget_service: AccountService = Depends(get_account_service),
    current_user=Depends(get_current_user),
):
    """
    Remove a specific account for the current user.

    Args:
        account_id: The ID of the account to remove.
        budget_service: Injected BudgetService instance.
        current_user: The authenticated user.

    Returns:
        Result of the account removal operation.
    """
    return budget_service.remove_account(account_id, current_user.id)
