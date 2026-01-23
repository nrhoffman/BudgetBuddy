import pytest
from pydantic import ValidationError
from app.models.user import UserRole, UserCreate, User

# -----------------------
# Test default role in UserCreate
# -----------------------
def test_usercreate_defaults_to_user_role():
    user = UserCreate(username="alice", email="alice@example.com", password="secret")
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.password == "secret"
    assert user.role == "user"


# -----------------------
# Test setting roles in UserCreate
# -----------------------
@pytest.mark.parametrize("role", ["user", "admin"])
def test_usercreate_can_set_role(role):
    user = UserCreate(username="bob", email="bob@example.com", password="secret", role=role)
    assert user.role == role


# -----------------------
# Test valid roles in User model
# -----------------------
@pytest.mark.parametrize("role", [UserRole.USER, UserRole.ADMIN])
def test_user_model_accepts_valid_role(role):
    user = User(
        id="123",
        username="alice",
        email="alice@example.com",
        hashed_password="hashed",
        role=role
    )
    assert user.role == role


# -----------------------
# Test invalid roles in User model
# -----------------------
@pytest.mark.parametrize("invalid_role", ["superuser", "manager", "guest"])
def test_user_model_rejects_invalid_role(invalid_role):
    with pytest.raises(ValidationError):
        User(
            id="123",
            username="alice",
            email="alice@example.com",
            hashed_password="hashed",
            role=invalid_role
        )
