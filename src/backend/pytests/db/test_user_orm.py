import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.user_orm import UserORM
from app.models.user import UserRole


# -----------------------
# Fixture: in-memory SQLite database
# -----------------------
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# -----------------------
# Parametrized creation of users
# -----------------------
@pytest.mark.parametrize(
    "user_id, username, email, hashed_password, role",
    [
        ("user_001", "alice", "alice@example.com", "hashed_pw_1", UserRole.USER),
        ("user_002", "bob", "bob@example.com", "hashed_pw_2", UserRole.ADMIN),
        ("user_003", "carol", "carol@example.com", "hashed_pw_3", None),
    ],
)
def test_user_orm_creation(db_session, user_id, username, email, hashed_password, role):
    user = UserORM(
        id=user_id,
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role or UserRole.USER,
    )
    db_session.add(user)
    db_session.commit()

    saved_user = db_session.query(UserORM).filter_by(id=user_id).first()
    assert saved_user is not None
    assert saved_user.id == user_id
    assert saved_user.username == username
    assert saved_user.email == email
    assert saved_user.hashed_password == hashed_password
    assert saved_user.role == (role or UserRole.USER)


# -----------------------
# Test unique constraints for username and email
# -----------------------
def test_user_orm_unique_constraints(db_session):
    user1 = UserORM(
        id="user_100",
        username="unique_user",
        email="unique@example.com",
        hashed_password="pw",
    )
    db_session.add(user1)
    db_session.commit()

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
