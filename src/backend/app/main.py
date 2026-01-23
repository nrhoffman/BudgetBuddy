from fastapi import FastAPI

from app.routes import auth, accounts, bank

app = FastAPI(title="BudgetBuddy API")

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(bank.router)
