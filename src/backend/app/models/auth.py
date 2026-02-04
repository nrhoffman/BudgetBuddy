"""
Schema for user login requests.

Defines the LoginRequest Pydantic model for the login endpoint.
"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """
    Request body for the user login endpoint.

    Attributes:
        username (str): The username of the user.
        password (str): The user's password.
    """

    username: str
    password: str
