"""Garmin Connect API client wrapper using garminconnect library."""

from __future__ import annotations

from datetime import datetime

from garminconnect import Garmin


class GarminClient:
    """Wrapper around garminconnect library for Garmin Connect API access."""

    def __init__(self, username: str, password: str):
        """Initialize Garmin client with credentials.

        Args:
            username: Garmin Connect email/username
            password: Garmin Connect password
        """
        self.username = username
        self.client = Garmin(username, password)
        self._authenticated = False

    def authenticate(self) -> bool:
        """Authenticate with Garmin Connect.

        Returns:
            True if authentication succeeded, False otherwise
        """
        try:
            self.client.login()
            self._authenticated = True
            return True
        except Exception:
            self._authenticated = False
            return False

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
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.client.get_activities(start, limit)

    def get_activity(self, activity_id: int) -> dict:
        """Fetch detailed information for a specific activity.

        Args:
            activity_id: Garmin activity ID

        Returns:
            Activity detail dictionary from Garmin API
        """
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.client.get_activity(activity_id)

    def get_user_profile(self) -> dict:
        """Fetch user profile information.

        Returns:
            User profile dictionary from Garmin API
        """
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.client.get_full_profile()

    def get_stats(self, date: str) -> dict:
        """Fetch daily stats for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Daily stats dictionary (resting HR, stress, steps, etc.)
        """
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.client.get_stats(date)

    def get_sleep_data(self, date: str) -> dict:
        """Fetch sleep data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Sleep data dictionary from Garmin API
        """
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.client.get_sleep_data(date)

    def get_hrv_data(self, date: str) -> dict:
        """Fetch HRV data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            HRV data dictionary from Garmin API
        """
        if not self._authenticated:
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
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.client.get_body_battery(start_date, end_date)
