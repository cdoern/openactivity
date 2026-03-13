"""OS keychain credential storage using the keyring library."""

from __future__ import annotations

import contextlib

import keyring

SERVICE_NAME = "openactivity-strava"

# Credential keys
CLIENT_ID = "client_id"
CLIENT_SECRET = "client_secret"
ACCESS_TOKEN = "access_token"
REFRESH_TOKEN = "refresh_token"
TOKEN_EXPIRY = "token_expiry"

_ALL_KEYS = [CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, REFRESH_TOKEN, TOKEN_EXPIRY]


def store_credential(key: str, value: str) -> None:
    """Store a credential in the OS keychain."""
    keyring.set_password(SERVICE_NAME, key, value)


def get_credential(key: str) -> str | None:
    """Retrieve a credential from the OS keychain. Returns None if not found."""
    return keyring.get_password(SERVICE_NAME, key)


def delete_credential(key: str) -> None:
    """Delete a credential from the OS keychain. Silently ignores if not found."""
    with contextlib.suppress(keyring.errors.PasswordDeleteError):
        keyring.delete_password(SERVICE_NAME, key)


def store_client_credentials(client_id: str, client_secret: str) -> None:
    """Store Strava API client credentials."""
    store_credential(CLIENT_ID, client_id)
    store_credential(CLIENT_SECRET, client_secret)


def get_client_credentials() -> tuple[str | None, str | None]:
    """Retrieve stored client ID and secret."""
    return get_credential(CLIENT_ID), get_credential(CLIENT_SECRET)


def store_tokens(access_token: str, refresh_token: str, expires_at: int) -> None:
    """Store OAuth tokens and expiry timestamp."""
    store_credential(ACCESS_TOKEN, access_token)
    store_credential(REFRESH_TOKEN, refresh_token)
    store_credential(TOKEN_EXPIRY, str(expires_at))


def get_tokens() -> tuple[str | None, str | None, int | None]:
    """Retrieve stored tokens. Returns (access_token, refresh_token, expires_at)."""
    access = get_credential(ACCESS_TOKEN)
    refresh = get_credential(REFRESH_TOKEN)
    expiry_str = get_credential(TOKEN_EXPIRY)
    expiry = int(expiry_str) if expiry_str else None
    return access, refresh, expiry


def delete_all_credentials() -> None:
    """Delete all stored credentials from the OS keychain."""
    for key in _ALL_KEYS:
        delete_credential(key)


def has_client_credentials() -> bool:
    """Check if client ID and secret are stored."""
    client_id, client_secret = get_client_credentials()
    return client_id is not None and client_secret is not None


def has_tokens() -> bool:
    """Check if OAuth tokens are stored."""
    access, refresh, _ = get_tokens()
    return access is not None and refresh is not None
