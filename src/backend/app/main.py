"""
Main FastAPI application entry point for BudgetBuddy.

This module defines the FastAPI application instance and registers all API
routers for authentication, account management, and banking operations.
It also sets up centralized exception handlers to return structured JSON
responses for known application-level errors.
"""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.exceptions import (
    AppError,
    ValidationError,
    NotFoundError,
    ConflictError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    BankingProviderError,
    ExternalServiceError,
)
from app.routes import auth, accounts, bank, user

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="BudgetBuddy API")

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(bank.router)
app.include_router(user.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.exception_handler(ValidationError)
async def validation_handler(_request: Request, exc: ValidationError):
    """
    Handle ValidationError exceptions.

    Returns a 400 Bad Request response with the error message.

    Args:
        _request (Request): FastAPI request object (unused).
        exc (ValidationError): The raised validation error.

    Returns:
        JSONResponse: HTTP 400 response with error details.
    """

    return JSONResponse(status_code=400, content=error_response(exc))


@app.exception_handler(NotFoundError)
async def not_found_handler(_request: Request, exc: NotFoundError):
    """
    Handle NotFoundError exceptions.

    Returns a 404 Not Found response with the error message.

    Args:
        _request (Request): FastAPI request object (unused).
        exc (NotFoundError): The raised not-found error.

    Returns:
        JSONResponse: HTTP 404 response with error details.
    """

    return JSONResponse(status_code=404, content=error_response(exc))


@app.exception_handler(ConflictError)
async def conflict_handler(_request: Request, exc: ConflictError):
    """
    Handle ConflictError exceptions.

    Returns a 409 Conflict response with the error message.

    Args:
        _request (Request): FastAPI request object (unused).
        exc (ConflictError): The raised conflict error.

    Returns:
        JSONResponse: HTTP 409 response with error details.
    """

    return JSONResponse(status_code=409, content=error_response(exc))


@app.exception_handler(AuthenticationError)
async def auth_handler(_request: Request, exc: AuthenticationError):
    """
    Handle AuthenticationError exceptions.

    Returns a 401 Unauthorized response with the error message.

    Args:
        _request (Request): FastAPI request object (unused).
        exc (AuthenticationError): The raised authentication error.

    Returns:
        JSONResponse: HTTP 401 response with error details.
    """

    return JSONResponse(status_code=401, content=error_response(exc))


@app.exception_handler(AuthorizationError)
async def authorization_handler(_request: Request, exc: AuthorizationError):
    """
    Handle AuthorizationError exceptions.

    Returns a 403 Forbidden response with the error message.

    Args:
        _request (Request): FastAPI request object (unused).
        exc (AuthorizationError): The raised authorization error.

    Returns:
        JSONResponse: HTTP 403 response with error details.
    """

    return JSONResponse(status_code=403, content=error_response(exc))


@app.exception_handler(DatabaseError)
async def database_handler(_request: Request, exc: DatabaseError):
    """
    Handle DatabaseError exceptions.

    Returns a 500 Internal Server Error response with error details.

    Args:
        _request (Request): FastAPI request object (unused).
        exc (DatabaseError): The raised database error.

    Returns:
        JSONResponse: HTTP 500 response with error details and extra info.
    """

    return JSONResponse(
        status_code=500,
        content=error_response(exc, details=getattr(exc, "details", None)),
    )


@app.exception_handler(BankingProviderError)
async def banking_handler(_request: Request, exc: BankingProviderError):
    """
    Handle BankingProviderError exceptions.

    Returns a 502 Bad Gateway response for external banking provider errors.

    Args:
        _request (Request): FastAPI request object (unused).
        exc (BankingProviderError): The raised banking provider error.

    Returns:
        JSONResponse: HTTP 502 response with error details and extra info.
    """

    return JSONResponse(
        status_code=502,  # Bad gateway for external provider errors
        content=error_response(exc, details=getattr(exc, "details", None)),
    )


@app.exception_handler(ExternalServiceError)
async def external_service_handler(_request: Request, exc: ExternalServiceError):
    """
    Handle ExternalServiceError exceptions.

    Returns a 502 Bad Gateway response for errors from external services
    (e.g., Plaid or other banking providers).

    Args:
        _request (Request): FastAPI request object (unused).
        exc (ExternalServiceError): The raised external service error.

    Returns:
        JSONResponse: HTTP 502 response with error details and additional info.
    """

    return JSONResponse(
        status_code=502,
        content=error_response(exc, details=exc.details),
    )


@app.exception_handler(AppError)
async def generic_app_error(_request: Request, exc: AppError):
    """
    Handle generic AppError exceptions.

    Returns a 500 Internal Server Error response for unexpected application errors.

    Args:
        _request (Request): FastAPI request object (unused).
        exc (AppError): The raised application error.

    Returns:
        JSONResponse: HTTP 500 response with error details.
    """

    return JSONResponse(status_code=500, content=error_response(exc))


def error_response(
    exc: Exception,
    *,
    details: object | None = None
) -> dict:
    """
    Build a canonical error response payload.

    Shape:
    {
        "error": {
            "type": "<ExceptionClass>",
            "message": "<human-readable message>",
            "details": <optional structured data>
        }
    }
    """
    return {
        "error": {
            "type": exc.__class__.__name__,
            "message": str(exc),
            "details": details,
        }
    }
