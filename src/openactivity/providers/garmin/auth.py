"""Garmin Connect authentication module with MFA support."""

from __future__ import annotations

from pathlib import Path

from openactivity.auth import keyring
from openactivity.providers.garmin.client import GarminClient


def authenticate(username: str, password: str) -> tuple[bool, str | None]:
    """Authenticate with Garmin Connect using username/password (supports MFA).

    This will prompt for MFA code if required. Tokens are saved for future use.

    Args:
        username: Garmin Connect email/username
        password: Garmin Connect password

    Returns:
        Tuple of (success, error_message)
        - (True, None) if authentication succeeded
        - (False, error_type) if authentication failed
    """
    client = GarminClient()

    success, error = client.authenticate_with_credentials(username, password)

    if success:
        # Store username for reference (but not password - we use tokens now)
        keyring.store_garmin_credentials(username, "TOKEN_BASED_AUTH")
        return True, None

    return False, error


def get_authenticated_client() -> tuple[GarminClient | None, str | None]:
    """Get an authenticated Garmin client using saved tokens.

    This reuses OAuth tokens from previous authentication, avoiding repeated logins.

    Returns:
        Tuple of (client, error_message)
        - (GarminClient, None) if authentication succeeded
        - (None, error_type) if authentication failed
    """
    client = GarminClient()

    # Try to authenticate with saved tokens first
    success, error = client.authenticate_with_tokens()

    if success:
        return client, None

    # No valid tokens found
    return None, error


def is_authenticated() -> bool:
    """Check if Garmin tokens exist.

    Returns:
        True if garth tokens are saved
    """
    tokens_dir = Path.home() / ".local" / "share" / "openactivity" / "garmin"
    token_file = tokens_dir / "tokens"
    return token_file.exists()


def logout() -> None:
    """Remove stored Garmin tokens and credentials."""
    # Remove garth tokens
    tokens_dir = Path.home() / ".local" / "share" / "openactivity" / "garmin"
    if tokens_dir.exists():
        import shutil

        shutil.rmtree(tokens_dir)

    # Remove keyring entry
    keyring.delete_garmin_credentials()
