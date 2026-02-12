"""
Domain models for raw provider data and related metadata.

This module defines immutable dataclasses representing raw events
from external banking providers. These classes encapsulate the
provider payload, user/item identity, cursor information for
incremental updates, and the timestamp of the event.
"""

from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime


@dataclass(frozen=True)
class Cursor:
    """
    Represents the state of a provider sync cursor for incremental updates.

    Attributes:
        before (Optional[str]): Previous cursor value before the sync.
        after (Optional[str]): Cursor value after the sync.
    """

    before: Optional[str] = None
    after: Optional[str] = None


@dataclass(frozen=True)
class Identity:
    """
    Represents the identity of the user and provider item associated
    with a raw provider event.

    Attributes:
        user_id (Optional[str]): ID of the user linked to the provider item.
        item_id (Optional[str]): Provider-specific item identifier.
    """

    user_id: Optional[str] = None
    item_id: Optional[str] = None


@dataclass(frozen=True)
class RawProviderData:
    """
    Immutable model for storing raw events from an external provider.

    Attributes:
        provider (str): Name of the external provider (e.g., 'plaid').
        endpoint (str): Name of the endpoint or API call that produced the event.
        payload (Dict): Raw JSON-like payload returned by the provider.
        identity (Identity): User and item identity associated with the event.
        cursor (Cursor): Cursor state for incremental syncs.
        occurred_at (Optional[datetime]): Timestamp when the event occurred.
    """

    provider: str
    endpoint: str
    payload: Dict
    identity: Identity = Identity()
    cursor: Cursor = Cursor()
    occurred_at: Optional[datetime] = None
