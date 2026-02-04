"""
Tests for the LoginRequest Pydantic schema.

Ensures required fields and type validation work as expected.
"""

import pytest
from pydantic import ValidationError
from app.models.auth import LoginRequest


# -----------------------
# Parametrized valid login requests
# -----------------------
@pytest.mark.parametrize(
    "data,expected_username,expected_password",
    [
        ({"username": "alice", "password": "secret"}, "alice", "secret"),
        ({"username": "bob", "password": "12345"}, "bob", "12345"),
        ({"username": "carol", "password": "pass!@#"}, "carol", "pass!@#"),
    ],
)
def test_login_request_valid(data, expected_username, expected_password):
    """Valid data should create a LoginRequest instance."""
    req = LoginRequest(**data)
    assert req.username == expected_username
    assert req.password == expected_password


# -----------------------
# Parametrized invalid login requests
# -----------------------
@pytest.mark.parametrize(
    "data",
    [
        ({"password": "secret"}),      # missing username
        ({"username": "alice"}),       # missing password
        ({"username": 123, "password": "secret"}),  # username wrong type
        ({"username": "alice", "password": 456}),   # password wrong type
        ({})                            # missing both
    ],
)
def test_login_request_invalid(data):
    """Invalid data should raise a ValidationError."""
    with pytest.raises(ValidationError):
        LoginRequest(**data)
