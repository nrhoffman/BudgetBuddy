"""
Banking API routes for managing connections to external banking providers.

This module defines endpoints for creating link tokens, exchanging public
tokens, and handling Plaid webhooks. Includes type hints, logging, and
dependency injection for BankingService and user authentication.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_banking_service, get_current_user
from app.models.exchange_token import ExchangeToken
from app.services.banking_service import BankingService

router = APIRouter(prefix="/api/bank", tags=["bank"])


@router.post("/create-link-token", response_model=dict[str, str])
def create_link_token(
    banking_service: BankingService = Depends(get_banking_service),
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    """
    Create a bank link token for the authenticated user.

    Args:
        banking_service: Injected BankingService instance.
        current_user: Authenticated user from JWT.

    Returns:
        Dictionary containing the provider-generated link token.
    """
    link_token = banking_service.create_bank_link_token(current_user.id)
    return {"link_token": link_token}


@router.post("/create-update-link-token", response_model=dict[str, str])
def create_update_link_token(
    institution_id: str = Query(...),
    banking_service: BankingService = Depends(get_banking_service),
    current_user=Depends(get_current_user),
) -> dict:
    link_token = banking_service.create_bank_update_link_token(
        current_user.id,
        institution_id,
    )
    return {"link_token": link_token}


@router.post("/exchange-token", response_model=dict[str, str])
def exchange_token(
    req: ExchangeToken,
    banking_service: BankingService = Depends(get_banking_service),
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    """
    Exchange a public token and sync bank accounts and transactions.

    Args:
        req: Request payload containing public token, institution ID, and name.
        banking_service: Injected BankingService instance.
        current_user: Authenticated user from JWT.

    Returns:
        Dictionary with a confirmation message.
    """
    banking_service.add_bank_institution(
        user_id=current_user.id,
        public_token=req.public_token,
        institution_id=req.institution_id,
        institution_name=req.institution_name,
    )
    return {"message": "Bank accounts synced"}

@router.post("/sync-institution-accounts", response_model=dict[str, Any])
def sync_institution_accounts(
    institution_id: str = Query(...),
    banking_service: BankingService = Depends(get_banking_service),
    current_user=Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get all bank accounts for the authenticated user.

    Args:
        banking_service: Injected BankingService instance.
        current_user: Authenticated user from JWT.

    Returns:
        Dictionary with account information.
    """
    accounts = banking_service.sync_bank_accounts(
        user_id=current_user.id,
        institution_id=institution_id
    )
    return {"status": "linked", "accounts_added": accounts}


@router.post("/webhooks/plaid")
async def plaid_webhook(
    payload: dict[str, Any],
    banking_service: BankingService = Depends(get_banking_service),
) -> dict[str, str]:
    """
    Handle Plaid webhook events.

    Args:
        payload: Webhook payload from Plaid.
        banking_service: Injected BankingService instance.

    Returns:
        Response from the banking service webhook handler.
    """
    banking_service.plaid_webhook(payload)
    return {"status": "ok"}
