from typing import Any
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.dependencies import get_banking_service, get_current_user
from app.models.exchange_token import ExchangeToken
from app.services.banking_service import BankingService

router = APIRouter(prefix="/api/bank", tags=["bank"])


@router.post("/create-link-token", response_model=dict[str, str])
def create_link_token(
    banking_service: BankingService = Depends(get_banking_service),
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    try:
        link_token = banking_service.create_bank_link_token(current_user.id)
        return {"link_token": link_token}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create link token"
        )


@router.post("/exchange-token", response_model=dict[str, str])
def exchange_token(
    req: ExchangeToken,
    banking_service: BankingService = Depends(get_banking_service),
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    try:
        banking_service.add_bank_institution(
            user_id=current_user.id,
            public_token=req.public_token,
            institution_id=req.institution_id,
            institution_name=req.institution_name,
        )
        return {"message": "Bank accounts synced"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to exchange token"
        )


@router.post("/get-accounts", response_model=dict[str, Any])
def get_accounts(
    institution_id: str = Query(...),
    banking_service: BankingService = Depends(get_banking_service),
    current_user=Depends(get_current_user),
) -> dict[str, Any]:
    try:
        accounts = banking_service.add_bank_accounts(
            user_id=current_user.id,
            institution_id=institution_id
        )
        return {"accounts": accounts}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve accounts"
        )


@router.post("/webhooks/plaid")
async def plaid_webhook(
    payload: dict[str, Any],
    banking_service: BankingService = Depends(get_banking_service),
) -> dict[str, str]:
    try:
        banking_service.plaid_webhook(payload)
        return {"status": "ok"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )
