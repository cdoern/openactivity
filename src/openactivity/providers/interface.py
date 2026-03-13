"""Shared provider interface for fitness platform integrations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@runtime_checkable
class Provider(Protocol):
    """Minimal shared interface that all providers must implement."""

    name: str

    def authenticate(self) -> dict:
        """Run the authentication flow. Return athlete info dict."""
        ...

    def revoke(self) -> None:
        """Remove all stored credentials."""
        ...

    def sync(self, session: Session, *, full: bool = False, detail: bool = True) -> dict:
        """Sync data from provider into local storage.

        Args:
            session: SQLAlchemy database session.
            full: If True, re-sync all data ignoring last sync timestamp.
            detail: If True, fetch detailed data (streams, laps, zones).

        Returns:
            Dict with sync summary (synced, new, updated, errors, etc.).
        """
        ...

    def is_authenticated(self) -> bool:
        """Check if valid credentials exist."""
        ...
