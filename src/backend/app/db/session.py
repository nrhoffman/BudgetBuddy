"""
Database configuration and session setup for the application.

Loads environment variables, initializes the SQLAlchemy engine, and
provides a session factory for ORM operations.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.logger import logger

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

DATABASE_DEBUG = os.getenv("DATABASE_DEBUG", "false").lower() == "true"

# SQLAlchemy engine
ENGINE = create_engine(
    DATABASE_URL,
    echo=DATABASE_DEBUG,
)

# Session factory
SESSIONLOCAL = sessionmaker(
    bind=ENGINE,
    expire_on_commit=False,
)

logger.info(
    "Database engine initialized",
    extra={"echo": DATABASE_DEBUG},
)
