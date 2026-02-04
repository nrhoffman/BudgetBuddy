import os
import json
import requests

from dotenv import load_dotenv

load_dotenv()

# ------------------------
# Configuration
# ------------------------
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
ACCESS_TOKEN = ""
PLAID_ENV = "https://sandbox.plaid.com"


url = f"{PLAID_ENV}/sandbox/transactions/create"

payload = {
    "client_id": PLAID_CLIENT_ID,
    "secret": PLAID_SECRET,
    "access_token": ACCESS_TOKEN,
    "transactions": [
        {
        "amount": 5.75,
        "description": "Starbucks",
        "date_posted": "2026-02-03",
        "date_transacted": "2026-02-03",
        "iso_currency_code": "USD",
        },
        {
        "amount": 42.30,
        "description": "Starbucks",
        "date_posted": "2026-02-02",
        "date_transacted": "2026-02-02",
        "iso_currency_code": "USD",
        },
        {
        "amount": -1500.00,
        "description": "United Airlines",
        "date_posted": "2026-02-01",
        "date_transacted": "2026-02-01",
        "iso_currency_code": "USD",
        },
        {
        "amount": 18.90,
        "description": "Kohls",
        "date_posted": "2026-01-29",
        "date_transacted": "2026-01-29",
        "iso_currency_code": "USD",
        },
        {
        "amount": 100.00,
        "description": "atm withdrawal",
        "date_posted": "2026-01-28",
        "date_transacted": "2026-01-28",
        "iso_currency_code": "USD",
        }
    ]
}

response = requests.post(url, json=payload)
print("Status code:", response.status_code)
print("Response body:", json.dumps(response.json(), indent=2))
