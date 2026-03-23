"""Garmin Connect authentication module."""

from __future__ import annotations

from openactivity.auth import keyring
from openactivity.providers.garmin.client import GarminClient


def authenticate(username: str, password: str) -> bool:
    """Authenticate with Garmin Connect and store credentials.

    Args:
        username: Garmin Connect email/username
        password: Garmin Connect password

    Returns:
        True if authentication succeeded and credentials were stored
    """
    client = GarminClient(username, password)

    if client.authenticate():
        keyring.store_garmin_credentials(username, password)
        return True

    return False


def get_authenticated_client() -> GarminClient | None:
    """Get an authenticated Garmin client using stored credentials.

    Returns:
        Authenticated GarminClient instance, or None if no credentials stored
        or authentication failed
    """
    username, password = keyring.get_garmin_credentials()

    if not username or not password:
        return None

    client = GarminClient(username, password)

    if client.authenticate():
        return client

    return None


def is_authenticated() -> bool:
    """Check if Garmin credentials are stored.

    Returns:
        True if credentials are stored in keyring
    """
    return keyring.has_garmin_credentials()


def logout() -> None:
    """Remove stored Garmin credentials from keyring."""
    keyring.delete_garmin_credentials()
