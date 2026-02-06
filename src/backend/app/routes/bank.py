"""
Banking API routes for managing connections to external banking providers.

This module defines endpoints for creating link tokens, exchanging public
tokens, and handling Plaid webhooks. Includes type hints, logging, and
dependency injection for BankingService and user authentication.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.logger import logger
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

    Raises:
        HTTPException: If token creation fails.
    """
    try:
        link_token = banking_service.create_bank_link_token(current_user.id)
        logger.debug("Created bank link token for user %s", current_user.id)
        return {"link_token": link_token}
    except Exception as exc:
        logger.exception(
            "Failed to create link token for user %s: %s",
            current_user.id,
            exc
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to create link token"
        ) from exc


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

    Raises:
        HTTPException: If token exchange or syncing fails.
    """
    try:
        banking_service.add_bank_institution(
            user_id=current_user.id,
            public_token=req.public_token,
            institution_id=req.institution_id,
            institution_name=req.institution_name,
        )
        logger.debug(
            "Exchanged public token and synced accounts for user %s", current_user.id
        )
        return {"message": "Bank accounts synced"}
    except Exception as exc:
        logger.exception(
            "Failed to exchange token for user %s with institution %s: %s",
            current_user.id,
            req.institution_id,
            exc
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to exchange token"
        ) from exc


@router.post("/get-accounts", response_model=dict[str, Any])
def get_accounts(
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
    try:
        accounts = banking_service.add_bank_accounts(
            user_id=current_user.id,
            institution_id=institution_id
        )
        logger.debug(
            "Retrieved accounts for user %s (institution_id=%s)",
            current_user.id,
            institution_id,
        )
        return accounts
    except Exception as exc:
        logger.exception(
            "Failed to retrieve accounts for user %s: %s",
            current_user.id,
            exc,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve accounts",
        ) from exc


@router.post("/webhooks/plaid")
async def plaid_webhook(
    payload: dict[str, Any],
    banking_service: BankingService = Depends(get_banking_service),
) -> Any:
    """
    Handle Plaid webhook events.

    Args:
        payload: Webhook payload from Plaid.
        banking_service: Injected BankingService instance.

    Returns:
        Response from the banking service webhook handler.

    Raises:
        HTTPException: If processing fails.
    """
    try:
        result = banking_service.plaid_webhook(payload)
        logger.debug("Processed Plaid webhook: %s", payload.get("webhook_type"))
        return result
    except Exception as exc:
        logger.exception("Failed to process Plaid webhook: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to process webhook"
        ) from exc
