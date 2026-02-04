"""
Parametrized tests for ExchangeToken Pydantic schema.
"""

import pytest
from pydantic import ValidationError
from app.models.exchange_token import ExchangeToken


# -----------------------
# Parametrized valid ExchangeToken inputs
# -----------------------
@pytest.mark.parametrize(
    "data, expected_public, expected_inst_id, expected_inst_name",
    [
        ({"public_token": "token_001"}, "token_001", None, None),
        ({"public_token": "token_002", "institution_id": "inst_001"},
         "token_002", "inst_001", None),
        ({"public_token": "token_003", "institution_name": "BankX"},
         "token_003", None, "BankX"),
        ({"public_token": "token_004", "institution_id": "inst_002",
          "institution_name": "BankY"},
         "token_004", "inst_002", "BankY"),
    ],
)
def test_exchange_token_valid(data, expected_public, expected_inst_id,
                              expected_inst_name):
    """Valid data should create an ExchangeToken instance."""
    token = ExchangeToken(**data)
    assert token.public_token == expected_public
    assert token.institution_id == expected_inst_id
    assert token.institution_name == expected_inst_name


# -----------------------
# Parametrized invalid ExchangeToken inputs
# -----------------------
@pytest.mark.parametrize(
    "data",
    [
        {},  # missing public_token
        {"public_token": None},  # None is invalid for required field
        {"public_token": 123},   # wrong type
    ],
)
def test_exchange_token_invalid(data):
    """Invalid data should raise a ValidationError."""
    with pytest.raises(ValidationError):
        ExchangeToken(**data)
