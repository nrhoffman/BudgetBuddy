"""
User API router.

Defines HTTP endpoints for user lifecycle operations, including
permanent deletion of user data. Routes delegate business logic
to the UserService and rely on dependency injection for
authentication and service resolution.
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_user_service, get_current_user
from app.services.user_service import UserService

router = APIRouter(prefix="/api/user", tags=["user"])


@router.delete("/delete-all")
def delete_all(
    user_service: UserService = Depends(get_user_service),
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    """
    Permanently delete the authenticated user's data.

    This endpoint triggers a full deletion of all user-associated
    financial records and the user account itself. The operation
    is irreversible.

    Args:
        user_service (UserService): Service responsible for handling
            user data deletion.
        current_user: Authenticated user resolved via dependency injection.

    Returns:
        dict[str, str]: Confirmation message indicating successful deletion.

    Raises:
        DatabaseError: If deletion fails at the service layer.
    """
    user_service.delete_all(current_user)
    return {"message": "All User Data Deleted"}
