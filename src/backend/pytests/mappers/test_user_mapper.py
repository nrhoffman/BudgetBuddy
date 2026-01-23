import pytest

from app.db.user_orm import UserORM
from app.models.user import User, UserRole
from app.mappers.user_mapper import orm_to_domain_user


# -----------------------
# Parametrize multiple users
# -----------------------
@pytest.mark.parametrize(
    "user_id, username, email, hashed_password, role",
    [
        ("user_001", "alice", "alice@example.com", "hashed_pw_1", UserRole.USER),
        ("user_002", "bob", "bob@example.com", "hashed_pw_2", UserRole.ADMIN),
        ("user_003", "carol", "carol@example.com", "hashed_pw_3", None),
    ]
)
def test_orm_to_domain_user(user_id, username, email, hashed_password, role):
    orm_user = UserORM(
        id=user_id,
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role or UserRole.USER
    )

    domain_user = orm_to_domain_user(orm_user)

    assert isinstance(domain_user, User)
    assert domain_user.id == user_id
    assert domain_user.username == username
    assert domain_user.email == email
    assert domain_user.hashed_password == hashed_password
    assert domain_user.role == (role or UserRole.USER)


# -----------------------
# Optional: test conversion preserves role enum
# -----------------------
def test_orm_to_domain_user_role_enum():
    orm_user = UserORM(
        id="user_010",
        username="dave",
        email="dave@example.com",
        hashed_password="hashed_pw_10",
        role=UserRole.ADMIN
    )

    domain_user = orm_to_domain_user(orm_user)

    assert isinstance(domain_user.role, UserRole)
    assert domain_user.role == UserRole.ADMIN
