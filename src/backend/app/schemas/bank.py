"""
Schema for exchanging a public bank token with the backend.
"""

from pydantic import BaseModel


class ExchangeTokenRequest(BaseModel):
    """
    Request body for exchanging a public token from a banking provider.

    Attributes:
        public_token: The public token received from the banking provider.
    """
    public_token: str
