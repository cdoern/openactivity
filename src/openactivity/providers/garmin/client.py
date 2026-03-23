"""Garmin Connect API client wrapper with MFA support via garth tokens."""

from __future__ import annotations

from pathlib import Path

import garth
from garminconnect import Garmin


class GarminClient:
    """Wrapper around garminconnect library with garth token support for MFA."""

    def __init__(self, tokens_dir: Path | None = None):
        """Initialize Garmin client with optional token directory.

        Args:
            tokens_dir: Directory to store garth tokens (default: ~/.local/share/openactivity/garmin)
        """
        self.tokens_dir = tokens_dir or (Path.home() / ".local" / "share" / "openactivity" / "garmin")
        self.tokens_dir.mkdir(parents=True, exist_ok=True)
        self.client = None
        self._authenticated = False

    def authenticate_with_tokens(self) -> tuple[bool, str | None]:
        """Authenticate using saved garth tokens.

        Returns:
            Tuple of (success, error_message)
            - (True, None) if authentication succeeded
            - (False, error_msg) if authentication failed
        """
        try:
            # Load saved tokens from our token directory
            garth.resume(str(self.tokens_dir))

            # Create Garmin client using the authenticated garth session
            self.client = Garmin(session_data=garth.client.dumps())
            self._authenticated = True
            return True, None

        except FileNotFoundError:
            return False, "no_tokens"
        except Exception as e:
            error_str = str(e)

            # Detect specific error types
            if "429" in error_str or "Too Many Requests" in error_str:
                return False, "rate_limit"
            elif "401" in error_str or "403" in error_str:
                return False, "invalid_tokens"
            else:
                return False, f"unknown: {error_str}"

    def authenticate_with_credentials(self, username: str, password: str) -> tuple[bool, str | None]:
        """Authenticate with username/password (supports MFA prompts).

        This will prompt for MFA code if required.

        Args:
            username: Garmin Connect email/username
            password: Garmin Connect password

        Returns:
            Tuple of (success, error_message)
            - (True, None) if authentication succeeded
            - (False, error_msg) if authentication failed
        """
        try:
            # Login with garth (handles MFA prompts interactively)
            garth.login(username, password)

            # Save tokens to our directory for future use
            garth.save(str(self.tokens_dir))

            # Create Garmin client using the authenticated session
            self.client = Garmin(session_data=garth.client.dumps())
            self._authenticated = True
            return True, None

        except Exception as e:
            self._authenticated = False
            error_str = str(e)

            # Detect specific error types
            if "429" in error_str or "Too Many Requests" in error_str:
                return False, "rate_limit"
            elif "401" in error_str or "403" in error_str:
                return False, "invalid_credentials"
            elif "MFA" in error_str or "two-factor" in error_str.lower():
                return False, "mfa_required"
            else:
                return False, f"unknown: {error_str}"

    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._authenticated

    def get_activities(self, start: int = 0, limit: int = 20) -> list[dict]:
        """Fetch activities from Garmin Connect.

        Args:
            start: Starting index for pagination
            limit: Number of activities to fetch

        Returns:
            List of activity dictionaries from Garmin API
        """
        if not self._authenticated or not self.client:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.client.get_activities(start, limit)

    def get_activity(self, activity_id: int) -> dict:
        """Fetch detailed information for a specific activity.

        Args:
            activity_id: Garmin activity ID

        Returns:
            Activity detail dictionary from Garmin API
        """
        if not self._authenticated or not self.client:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.client.get_activity(activity_id)

    def get_user_profile(self) -> dict:
        """Fetch user profile information.

        Returns:
            User profile dictionary from Garmin API
        """
        if not self._authenticated or not self.client:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.client.get_full_profile()

    def get_stats(self, date: str) -> dict:
        """Fetch daily stats for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Daily stats dictionary (resting HR, stress, steps, etc.)
        """
        if not self._authenticated or not self.client:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.client.get_stats(date)

    def get_sleep_data(self, date: str) -> dict:
        """Fetch sleep data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Sleep data dictionary from Garmin API
        """
        if not self._authenticated or not self.client:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.client.get_sleep_data(date)

    def get_hrv_data(self, date: str) -> dict:
        """Fetch HRV data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            HRV data dictionary from Garmin API
        """
        if not self._authenticated or not self.client:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.client.get_hrv_data(date)

    def get_body_battery(self, start_date: str, end_date: str) -> list[dict]:
        """Fetch Body Battery data for a date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of Body Battery data points
        """
        if not self._authenticated or not self.client:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.client.get_body_battery(start_date, end_date)
