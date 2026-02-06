"""
Account API endpoints for managing user financial accounts.

Provides routes to retrieve, update, and remove accounts, as well as
update user-editable transaction fields. Includes type hints, logging,
and proper HTTPException handling.
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_account_service, get_current_user
from app.models.transaction import UpdateTransaction
from app.services.account_service import AccountService
from app.logger import logger

router = APIRouter(prefix="/api/accounts", tags=["accounts"])

# -----------------------
# Account Routes
# -----------------------
@router.get("/get-accounts", response_model=Dict[str, Any])
def get_accounts(
    account_service: AccountService = Depends(get_account_service),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Retrieve all financial accounts for the current user.

    Args:
        account_service: Injected AccountService instance.
        current_user: The authenticated user.

    Returns:
        Dict containing the list of accounts under the "accounts" key.
    """
    try:
        accounts = account_service.get_user_financial_snapshot(current_user.id)
        logger.debug(
            "Retrieved %d accounts for user %s",
            len(accounts),
            current_user.id
        )
        return {"accounts": accounts}
    except Exception as exc:
        logger.exception("Failed to fetch accounts for user %s", current_user.id)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch accounts"
        ) from exc


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

    Returns:
        Result of the account update operation.
    """
    try:
        result = account_service.update_account(
            account_id=account_id,
            user_id=current_user.id,
            account_name=account_name,
        )
        logger.debug("Updated account %s for user %s", account_id, current_user.id)
        return result
    except Exception as exc:
        logger.exception(
            "Failed to update account %s for user %s",
            account_id,
            current_user.id
        )
        raise HTTPException(status_code=500, detail="Failed to update account") from exc


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

    Returns:
        Result of the account removal operation.
    """
    try:
        result = account_service.remove_account(account_id, current_user.id)
        logger.debug(
            "Removed account %s for user %s",
            account_id,
            current_user.id
        )
        return result
    except Exception as exc:
        logger.exception(
            "Failed to remove account %s for user %s",
            account_id,
            current_user.id
        )
        raise HTTPException(status_code=500, detail="Failed to remove account") from exc

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
) -> Dict[str, str]:
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

    Raises:
        HTTPException: 404 if the transaction does not exist or
        does not belong to the account.
    """
    try:
        existing_tx_list = account_service.txn_repo.get_by_ids([transaction_id])
        if not existing_tx_list:
            logger.warning(
                "Transaction %s not found for user %s",
                transaction_id,
                current_user.id
            )
            raise HTTPException(status_code=404, detail="Transaction not found")

        existing_tx = existing_tx_list[0]
        if existing_tx.account_id != account_id:
            logger.warning(
                "Transaction %s does not belong to account %s for user %s",
                transaction_id,
                account_id,
                current_user.id,
            )
            raise HTTPException(status_code=404, detail="Transaction not found")

        updated_tx = existing_tx.model_copy(
            update=payload.model_dump(exclude_unset=True)
        )
        account_service.apply_transaction_changes(
            user_id=current_user.id,
            added=[],
            modified=[updated_tx],
            removed=[],
        )
        logger.debug(
            "Updated transaction %s for account %s, user %s",
            transaction_id,
            account_id,
            current_user.id
        )
        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Failed to update transaction %s for account %s, user %s: %s",
            transaction_id,
            account_id,
            current_user.id,
            exc
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to update transaction"
        ) from exc

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
    try:
        institutions = account_service.get_institutions(user_id=current_user.id)
        logger.debug(
            "Retrieved %d institutions for user %s",
            len(institutions),
            current_user.id
        )
        return institutions
    except Exception as exc:
        logger.exception(
            "Failed to fetch institutions for user %s: %s",
            current_user.id,
            exc
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch institutions"
        ) from exc
