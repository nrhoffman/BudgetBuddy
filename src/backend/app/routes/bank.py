"""
Banking API routes.

This module defines endpoints for interacting with external banking
providers, including creating link tokens and exchanging public tokens
to sync bank accounts and transactions.
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_banking_service, get_current_user
from app.schemas.bank import ExchangeTokenRequest
from app.services.banking_service import BankingService

router = APIRouter(prefix="/api/bank", tags=["bank"])


@router.post("/create-link-token")
def create_link_token(
    banking_service: BankingService = Depends(get_banking_service),
    current_user=Depends(get_current_user),
):
    """
    Create a bank link token for the authenticated user.

    Args:
        banking_service: BankingService dependency.
        current_user: Authenticated user from JWT.

    Returns:
        dict: Provider-generated link token.
    """
    link_token = banking_service.create_bank_link_token(current_user.id)
    return {"link_token": link_token}


@router.post("/exchange-token")
def exchange_token(
    req: ExchangeTokenRequest,
    banking_service: BankingService = Depends(get_banking_service),
    current_user=Depends(get_current_user),
):
    """
    Exchange a public token and sync bank accounts and transactions.

    Args:
        req: Request payload containing public token.
        banking_service: BankingService dependency.
        current_user: Authenticated user from JWT.

    Returns:
        dict: Confirmation message.
    """
    banking_service.add_bank_accounts(current_user.id, req.public_token)
    return {"message": "Bank accounts synced"}
