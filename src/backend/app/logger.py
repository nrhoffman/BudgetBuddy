"""
Application-wide logger setup for Budget Buddy.

Configures console and rotating file handlers, log levels from .env,
and prevents duplicate propagation to root loggers.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# Logger setup
# -----------------------------
logger = logging.getLogger("budget_app")

if not logger.hasHandlers():
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    log_file_path = os.getenv("LOG_FILE", "log/budget_app.log")
    if log_file_path:
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=10_000_000, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

logger.propagate = False

# Prevent uvicorn default logger from propagating
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.propagate = False

logger.info("Logger initialized successfully")
