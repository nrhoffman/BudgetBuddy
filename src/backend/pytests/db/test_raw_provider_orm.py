import pytest
from sqlalchemy import create_engine, Column, String, DateTime, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column
from uuid import uuid4
from datetime import datetime, timezone

Base = declarative_base()

# ---------- Model for testing ----------
class RawProviderORM(Base):
    __tablename__ = "raw_provider_events"

    # UUID uses a String variant for SQLite
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True).with_variant(String(36), "sqlite"),
        primary_key=True,
        default=lambda: str(uuid4()),
        doc="Primary key UUID for the raw event."
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)

    # JSONB uses a JSON variant for SQLite
    payload: Mapped[dict] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"),
        nullable=False,
        doc="Raw JSON payload returned by the provider."
    )

    cursor_before: Mapped[str] = mapped_column(String, nullable=True)
    cursor_after: Mapped[str] = mapped_column(String, nullable=True)

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("provider", "endpoint", "cursor_before", "cursor_after", name="uq_raw_provider_cursor"),
    )

# ---------- Pytest Fixtures ----------
@pytest.fixture
def engine():
    return create_engine("sqlite:///:memory:", echo=False)

@pytest.fixture
def db_session(engine):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

# ---------- Example Tests ----------
def test_raw_provider_orm_creation(db_session):
    # Create a sample row
    row = RawProviderORM(
        provider="paypal-invoices",
        endpoint="update-user_003",
        payload={"some": "data"}
    )
    db_session.add(row)
    db_session.commit()

    retrieved = db_session.query(RawProviderORM).first()
    assert retrieved is not None
    assert retrieved.provider == "paypal-invoices"
    assert retrieved.payload["some"] == "data"

def test_raw_provider_orm_default_fetched_at(db_session):
    row = RawProviderORM(
        provider="stripe-payments",
        endpoint="payment-success",
        payload={"amount": 100}
    )
    db_session.add(row)
    db_session.commit()

    retrieved = db_session.query(RawProviderORM).first()
    assert retrieved.fetched_at is not None
    assert isinstance(retrieved.fetched_at, datetime)

def test_raw_provider_orm_unique_constraint(db_session):
    row1 = RawProviderORM(
        provider="paypal",
        endpoint="update",
        payload={"x": 1},
        cursor_before="abc",
        cursor_after="def"
    )
    row2 = RawProviderORM(
        provider="paypal",
        endpoint="update",
        payload={"x": 2},
        cursor_before="abc",
        cursor_after="def"
    )
    db_session.add(row1)
    db_session.commit()

    db_session.add(row2)
    with pytest.raises(Exception):
        db_session.commit()  # Should raise unique constraint violation
