"""
Celery application configuration for BudgetBuddy.

This module sets up the Celery app with Redis as both the broker and result backend.
It also automatically discovers tasks in the `app.tasks` package.
"""

from typing import Final

from celery import Celery

# Redis broker and result backend URLs
CELERY_BROKER_URL: Final[str] = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND: Final[str] = "redis://127.0.0.1:6379/0"

# Initialize Celery application
celery_app: Celery = Celery(
    "budgetbuddy",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)
"""Celery application instance for scheduling and executing tasks."""

# Automatically discover tasks from the specified modules
celery_app.autodiscover_tasks(
    ["app.tasks"]
)
