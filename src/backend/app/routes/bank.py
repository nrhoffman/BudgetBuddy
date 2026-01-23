from fastapi import APIRouter, Depends
from app.dependencies import get_budget_service, get_current_user
from app.schemas.bank import ExchangeTokenRequest
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/api/bank", tags=["bank"])

@router.post("/create-link-token")
def create_link_token(
    budget_service: BudgetService = Depends(get_budget_service),
    current_user=Depends(get_current_user)
):
    return {"link_token": budget_service.create_bank_link_token(current_user.id)}

@router.post("/exchange-token")
def exchange_token(
    req: ExchangeTokenRequest,
    budget_service: BudgetService = Depends(get_budget_service),
    current_user=Depends(get_current_user),
):
    budget_service.add_bank_accounts(current_user.id, req.public_token)
    return {"message": "Bank accounts synced"}
