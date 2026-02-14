"""
Convert ORM models to domain models.

Provides utility function to transform UserORM instances into their corresponding
domain model representation.
"""

from app.db.user_orm import UserORM
from app.models.user import User


def orm_to_domain_user(orm: UserORM) -> User:
    """
    Convert a UserORM instance to a domain User.

    Args:
        orm (UserORM): The ORM user object.

    Returns:
        User: The domain user object.
    """
    return User(
        id=orm.id,
        username=orm.username,
        email=orm.email,
        password=orm.hashed_password,
        hashed_password=orm.hashed_password,
        role=orm.role,
    )
