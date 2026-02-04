import os
import json
import requests

# ------------------------
# Configuration
# ------------------------
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
ACCESS_TOKEN = "access-sandbox-247cba53-8112-4982-9256-1c697a0fd422"
PLAID_ENV = "https://sandbox.plaid.com"


url = f"{PLAID_ENV}/sandbox/transactions/create"

payload = {
    "client_id": PLAID_CLIENT_ID,
    "secret": PLAID_SECRET,
    "access_token": ACCESS_TOKEN,
    "transactions": [
        {
            "account_id": "WQ7R1RVWy7TeK1p8yL5XHRPx4kQvLDuxo4jar",
            "amount": 100.50,
            "date_transacted": "2025-02-20",
            "date_posted": "2025-02-20",
            "description": "Test Purchase A"
        },
        {
            "account_id": "WQ7R1RVWy7TeK1p8yL5XHRPx4kQvLDuxo4jar",
            "amount": -25.75,
            "date_transacted": "2025-02-21",
            "date_posted": "2025-02-21",
            "description": "Refund B",
            "iso_currency_code": "USD"
        }
    ]
}

response = requests.post(url, json=payload)
print("Status code:", response.status_code)
print("Response body:", json.dumps(response.json(), indent=2))
