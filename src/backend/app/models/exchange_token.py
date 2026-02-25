"""
Schema for exchange token requests.

Defines the ExchangeToken Pydantic model for token exchange operations.
"""

from typing import Optional
from pydantic import BaseModel


class ExchangeToken(BaseModel):
    """
    Model representing a request to exchange a public token.

    Attributes:
        public_token (str): The public token provided by the client.
        institution_id (Optional[str]): Optional institution ID.
        institution_name (Optional[str]): Optional institution name.
    """

    public_token: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    institution_logo: Optional[str] = None
