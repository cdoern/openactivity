"""Strava API client wrapper with automatic token refresh and rate limiting."""

from __future__ import annotations

import os
import time

# Silence stravalib warnings about missing env vars — we use keyring instead
os.environ.setdefault("SILENCE_TOKEN_WARNINGS", "true")

from stravalib import Client  # noqa: E402

from openactivity.auth.keyring import get_tokens, has_tokens
from openactivity.providers.strava.oauth import is_token_expired, refresh_access_token


class RateLimitInfo:
    """Tracks Strava API rate limit status."""

    def __init__(self) -> None:
        self.short_limit: int = 200  # 15-minute window
        self.daily_limit: int = 2000
        self.short_usage: int = 0
        self.daily_usage: int = 0

    def update_from_headers(self, limit: str | None, usage: str | None) -> None:
        """Update rate limit info from response headers."""
        if limit:
            parts = limit.split(",")
            if len(parts) == 2:
                self.short_limit = int(parts[0].strip())
                self.daily_limit = int(parts[1].strip())
        if usage:
            parts = usage.split(",")
            if len(parts) == 2:
                self.short_usage = int(parts[0].strip())
                self.daily_usage = int(parts[1].strip())

    @property
    def short_remaining(self) -> int:
        return max(0, self.short_limit - self.short_usage)

    @property
    def daily_remaining(self) -> int:
        return max(0, self.daily_limit - self.daily_usage)

    @property
    def is_rate_limited(self) -> bool:
        return self.short_remaining == 0 or self.daily_remaining == 0

    def seconds_until_reset(self) -> int:
        """Estimate seconds until the 15-minute window resets."""
        now = time.time()
        # 15-minute windows reset at 0, 15, 30, 45 past the hour
        minutes_past = (now % 3600) / 60
        current_window_start = (int(minutes_past) // 15) * 15
        next_reset = current_window_start + 15
        seconds_remaining = int((next_reset - minutes_past) * 60)
        return max(1, seconds_remaining)


def get_strava_client() -> Client:
    """Get an authenticated stravalib Client with valid tokens.

    Automatically refreshes the access token if expired.

    Returns:
        Authenticated stravalib Client.

    Raises:
        RuntimeError: If no credentials are stored.
    """
    if not has_tokens():
        msg = "Not authenticated. Run 'openactivity strava auth' first."
        raise RuntimeError(msg)

    if is_token_expired():
        refresh_access_token()

    access_token, _, _ = get_tokens()
    client = Client(access_token=access_token)
    return client


# Module-level rate limit tracker
rate_limit = RateLimitInfo()
