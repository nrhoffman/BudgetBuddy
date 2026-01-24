"""Main FastAPI application entry point for BudgetBuddy.

Defines the FastAPI app instance and includes all API routers
for authentication, account management, and banking operations.
"""

from fastapi import FastAPI

from app.routes import auth, accounts, bank

app = FastAPI(title="BudgetBuddy API")

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(bank.router)
