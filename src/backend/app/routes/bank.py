"""
Banking API routes.

This module defines endpoints for interacting with external banking
providers, including creating link tokens and exchanging public tokens
to sync bank accounts and transactions.
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_budget_service, get_current_user
from app.schemas.bank import ExchangeTokenRequest
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/api/bank", tags=["bank"])


@router.post("/create-link-token")
def create_link_token(
    budget_service: BudgetService = Depends(get_budget_service),
    current_user=Depends(get_current_user),
):
    """
    Create a bank link token for the authenticated user.

    This token is used by the frontend to initiate the bank linking
    flow with the external banking provider.

    Args:
        budget_service: Injected BudgetService instance.
        current_user: Authenticated user from dependency injection.

    Returns:
        A dictionary containing the generated link token.
    """
    link_token = budget_service.create_bank_link_token(current_user.id)
    return {"link_token": link_token}


@router.post("/exchange-token")
def exchange_token(
    req: ExchangeTokenRequest,
    budget_service: BudgetService = Depends(get_budget_service),
    current_user=Depends(get_current_user),
):
    """
    Exchange a public token for permanent access and sync bank data.

    This endpoint exchanges the public token returned by the banking
    provider, links the user's bank accounts, and imports recent
    transactions.

    Args:
        req: Request payload containing the public token.
        budget_service: Injected BudgetService instance.
        current_user: Authenticated user from dependency injection.

    Returns:
        Confirmation message once bank accounts are synced.
    """
    budget_service.add_bank_accounts(current_user.id, req.public_token)
    return {"message": "Bank accounts synced"}
