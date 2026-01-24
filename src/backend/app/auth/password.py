"""
Password hashing and verification utilities using passlib.

This module provides functions to hash passwords and verify them securely
using the Argon2 hashing scheme.
"""

from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from app.logger import logger

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using Argon2.

    Args:
        password (str): The plaintext password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a hashed password.

    Handles exceptions for unknown or invalid hash formats.

    Args:
        plain_password (str): The plaintext password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (UnknownHashError, ValueError) as exc:
        logger.error(f"Password hash verification failed: {exc}", exc_info=True)
        return False
