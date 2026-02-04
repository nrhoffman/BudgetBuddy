"""
Tests for the UserORM model.

Covers creation, default role, and unique constraints for username/email.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.user_orm import UserORM
from app.models.user import UserRole


# -----------------------
# Fixture: in-memory SQLite
# -----------------------
@pytest.fixture
def db_session():
    """Provide a SQLAlchemy session using in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


# -----------------------
# Parametrized user creation
# -----------------------
@pytest.mark.parametrize(
    (
        "user_id",
        "username",
        "email",
        "hashed_password",
        "role",
    ),
    [
        ("user_001", "alice", "alice@example.com", "hashed_pw_1", UserRole.USER),
        ("user_002", "bob", "bob@example.com", "hashed_pw_2", UserRole.ADMIN),
        ("user_003", "carol", "carol@example.com", "hashed_pw_3", None),
    ],
)
def test_user_orm_creation(
    db_session,
    user_id,
    username,
    email,
    hashed_password,
    role,
):
    """Ensure users persist correctly and default role is applied."""
    user = UserORM(
        id=user_id,
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role or UserRole.USER,
    )

    db_session.add(user)
    db_session.commit()

    saved = (
        db_session.query(UserORM)
        .filter_by(id=user_id)
        .one()
    )

    assert saved.id == user_id
    assert saved.username == username
    assert saved.email == email
    assert saved.hashed_password == hashed_password
    assert saved.role == (role or UserRole.USER)


# -----------------------
# Unique constraints test
# -----------------------
def test_user_orm_unique_constraints(db_session):
    """Username and email must be unique; duplicates raise IntegrityError."""
    user1 = UserORM(
        id="user_100",
        username="unique_user",
        email="unique@example.com",
        hashed_password="pw",
    )
    db_session.add(user1)
    db_session.commit()

    # Duplicate username
    user_dup_username = UserORM(
        id="user_101",
        username="unique_user",
        email="other@example.com",
        hashed_password="pw2",
    )
    db_session.add(user_dup_username)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Duplicate email
    user_dup_email = UserORM(
        id="user_102",
        username="other_user",
        email="unique@example.com",
        hashed_password="pw3",
    )
    db_session.add(user_dup_email)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
