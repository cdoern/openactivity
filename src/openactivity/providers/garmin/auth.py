"""Garmin Connect authentication module."""

from __future__ import annotations

from openactivity.auth import keyring
from openactivity.providers.garmin.client import GarminClient


def authenticate(username: str, password: str) -> tuple[bool, str | None]:
    """Authenticate with Garmin Connect and store credentials.

    Args:
        username: Garmin Connect email/username
        password: Garmin Connect password

    Returns:
        Tuple of (success, error_message)
        - (True, None) if authentication succeeded
        - (False, error_type) if authentication failed
    """
    client = GarminClient(username, password)

    success, error = client.authenticate()

    if success:
        keyring.store_garmin_credentials(username, password)
        return True, None

    return False, error


def get_authenticated_client() -> tuple[GarminClient | None, str | None]:
    """Get an authenticated Garmin client using stored credentials.

    Returns:
        Tuple of (client, error_message)
        - (GarminClient, None) if authentication succeeded
        - (None, error_type) if authentication failed
    """
    username, password = keyring.get_garmin_credentials()

    if not username or not password:
        return None, "no_credentials"

    client = GarminClient(username, password)

    success, error = client.authenticate()

    if success:
        return client, None

    return None, error


def is_authenticated() -> bool:
    """Check if Garmin credentials are stored.

    Returns:
        True if credentials are stored in keyring
    """
    return keyring.has_garmin_credentials()


def logout() -> None:
    """Remove stored Garmin credentials from keyring."""
    keyring.delete_garmin_credentials()
