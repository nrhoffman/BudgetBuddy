"""
Schema for user login requests.
"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """
    Request body for user login endpoint.

    Attributes:
        username: The username of the user.
        password: The user's password.
    """
    username: str
    password: str
