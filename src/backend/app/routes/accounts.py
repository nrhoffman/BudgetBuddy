"""
Accounts API endpoints for managing user financial accounts.
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_budget_service, get_current_user
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("/get-accounts")
def get_accounts(
    budget_service: BudgetService = Depends(get_budget_service),
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
    accounts = budget_service.get_user_financial_snapshot(current_user.id)
    return {"accounts": accounts}


@router.delete("/remove-account/{account_id}")
def remove_account(
    account_id: str,
    budget_service: BudgetService = Depends(get_budget_service),
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
