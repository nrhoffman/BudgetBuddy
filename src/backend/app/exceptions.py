"""
Application-wide exception definitions.

This module defines the base exception hierarchy used throughout the
application, including validation, authentication, database, and
external service errors. These exceptions are intended to be raised
within service and repository layers and handled at the API or task
boundary.
"""

from typing import Optional, Any

from sqlalchemy.exc import SQLAlchemyError


# ---------------------------
# Base Exceptions
# ---------------------------
class AppError(Exception):
    """
    Base class for all application-level exceptions.

    Attributes:
        details (dict): Optional structured metadata describing the error.
    """

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


# ---------------------------
# Validation and Input Errors
# ---------------------------
class ValidationError(AppError):
    """Raised when user input is invalid or missing required fields."""


class AuthenticationError(AppError):
    """Raised when login or token validation fails."""


class AuthorizationError(AppError):
    """Raised when a user attempts an action they are not permitted to do."""


# ---------------------------
# Resource Errors
# ---------------------------
class NotFoundError(AppError):
    """Raised when an entity (account, transaction, user, institution) is not found."""


class ConflictError(AppError):
    """Raised when a resource conflicts with an existing entity (e.g., username/email
    exists).
    """


# ---------------------------
# Database / ORM Errors
# ---------------------------
class DatabaseError(AppError):
    """Raised when a database operation fails (SQLAlchemy, commit, query, etc.)."""


# ---------------------------
# Banking / Plaid Errors
# ---------------------------
class BankingProviderError(AppError):
    """Generic error for banking provider failures (Plaid, Yodlee, etc.)."""


class BankTokenMissingError(BankingProviderError):
    """Raised when no bank token exists for the user/institution."""


class BankLinkError(BankingProviderError):
    """Raised when linking a bank account fails."""


class TransactionSyncError(BankingProviderError):
    """Raised when transaction synchronization fails."""


# External Provider Errors
class ExternalServiceError(AppError):
    """Raised when an external service (e.g., Plaid/Banking provider) fails."""


# ---------------------------
# Utility to wrap exceptions
# ---------------------------
def wrap_db_exception(
        exc: Exception,
        message: str = "Database operation failed"
) -> DatabaseError:
    """
    Wrap a SQLAlchemy exception in a DatabaseError.

    Args:
        exc: The original exception.
        message: Optional override error message.

    Returns:
        DatabaseError: Wrapped database exception.
    """

    if isinstance(exc, SQLAlchemyError):
        return DatabaseError(
            message,
            details={"original_exception": str(exc)}
        )

    return DatabaseError(
        message,
        details={"original_exception": str(exc)}
    )
