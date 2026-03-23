"""OS keychain credential storage using the keyring library."""

from __future__ import annotations

import contextlib

import keyring

SERVICE_NAME = "openactivity-strava"
GARMIN_SERVICE_NAME = "openactivity-garmin"

# Strava credential keys
CLIENT_ID = "client_id"
CLIENT_SECRET = "client_secret"
ACCESS_TOKEN = "access_token"
REFRESH_TOKEN = "refresh_token"
TOKEN_EXPIRY = "token_expiry"

_ALL_KEYS = [CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, REFRESH_TOKEN, TOKEN_EXPIRY]

# Garmin credential keys
GARMIN_USERNAME = "username"
GARMIN_PASSWORD = "password"

_GARMIN_KEYS = [GARMIN_USERNAME, GARMIN_PASSWORD]


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


# Garmin credential functions


def store_garmin_credentials(username: str, password: str) -> None:
    """Store Garmin Connect username and password."""
    keyring.set_password(GARMIN_SERVICE_NAME, GARMIN_USERNAME, username)
    keyring.set_password(GARMIN_SERVICE_NAME, GARMIN_PASSWORD, password)


def get_garmin_credentials() -> tuple[str | None, str | None]:
    """Retrieve stored Garmin credentials. Returns (username, password)."""
    username = keyring.get_password(GARMIN_SERVICE_NAME, GARMIN_USERNAME)
    password = keyring.get_password(GARMIN_SERVICE_NAME, GARMIN_PASSWORD)
    return username, password


def delete_garmin_credentials() -> None:
    """Delete all Garmin credentials from the OS keychain."""
    for key in _GARMIN_KEYS:
        with contextlib.suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(GARMIN_SERVICE_NAME, key)


def has_garmin_credentials() -> bool:
    """Check if Garmin username and password are stored."""
    username, password = get_garmin_credentials()
    return username is not None and password is not None
