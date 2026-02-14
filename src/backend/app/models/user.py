"""
Pydantic models for user management.
"""

import enum
from typing import Optional
from pydantic import BaseModel


class UserRole(str, enum.Enum):
    """
    Enumeration of possible user roles.
    """
    ADMIN = "admin"
    USER = "user"


class UserCreate(BaseModel):
    """
    Model for creating a new user.

    Attributes:
        username: Desired username.
        email: User's email address.
        password: Plain text password.
        role: User role, defaults to "user".
    """
    username: str
    email: str
    password: str
    role: str = "user"


class User(BaseModel):
    """
    Represents a user in the system.

    Attributes:
        id: Unique identifier for the user.
        username: User's username.
        email: User's email address.
        password: raw password
        hashed_password: Hashed password for authentication.
        role: Role of the user (admin or user).
    """
    id: str
    username: str
    email: str
    password: str
    hashed_password: Optional[str] = None
    role: UserRole = UserRole.USER
