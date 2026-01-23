from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    Inherit from this class when defining ORM models to ensure consistent
    metadata and mapping configuration.
    """
    pass
