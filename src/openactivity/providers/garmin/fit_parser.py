"""FIT file parser using fitparse library."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fitparse import FitFile

if TYPE_CHECKING:
    from pathlib import Path


class FitActivityParser:
    """Parse Garmin FIT files into activity data."""

    def __init__(self, fit_file_path: Path):
        """Initialize parser with FIT file path.

        Args:
            fit_file_path: Path to .fit file
        """
        self.fit_file_path = fit_file_path
        self.fit = FitFile(str(fit_file_path))

    def parse(self) -> dict | None:
        """Parse FIT file and extract activity data.

        Returns:
            Dictionary with activity data, or None if not an activity file
        """
        activity_data = {
            "provider": "garmin",
            "provider_id": None,  # Will use file hash or timestamp
            "name": None,
            "type": None,
            "sport_type": None,
            "start_date": None,
            "start_date_local": None,
            "distance": 0.0,
            "moving_time": 0,
            "elapsed_time": 0,
            "total_elevation_gain": 0.0,
            "average_speed": 0.0,
            "max_speed": 0.0,
            "average_heartrate": None,
            "max_heartrate": None,
            "average_cadence": None,
            "average_watts": None,
            "max_watts": None,
            "calories": None,
            "has_heartrate": False,
            "has_power": False,
        }

        # Parse session message (contains summary data)
        for record in self.fit.get_messages("session"):
            for field in record:
                field_name = field.name
                field_value = field.value

                if field_name == "start_time":
                    activity_data["start_date"] = field_value
                    activity_data["start_date_local"] = field_value
                elif field_name == "sport":
                    activity_data["sport_type"] = field_value
                    activity_data["type"] = self._normalize_activity_type(field_value)
                elif field_name == "total_distance":
                    activity_data["distance"] = field_value  # meters
                elif field_name == "total_elapsed_time":
                    activity_data["elapsed_time"] = int(field_value)  # seconds
                elif field_name == "total_timer_time":
                    activity_data["moving_time"] = int(field_value)  # seconds
                elif field_name == "total_ascent":
                    activity_data["total_elevation_gain"] = field_value  # meters
                elif field_name == "avg_speed":
                    activity_data["average_speed"] = field_value  # m/s
                elif field_name == "max_speed":
                    activity_data["max_speed"] = field_value  # m/s
                elif field_name == "avg_heart_rate":
                    activity_data["average_heartrate"] = field_value
                    activity_data["has_heartrate"] = True
                elif field_name == "max_heart_rate":
                    activity_data["max_heartrate"] = field_value
                elif field_name == "avg_cadence":
                    activity_data["average_cadence"] = field_value
                elif field_name == "avg_power":
                    activity_data["average_watts"] = field_value
                    activity_data["has_power"] = True
                elif field_name == "max_power":
                    activity_data["max_watts"] = field_value
                elif field_name == "total_calories":
                    activity_data["calories"] = field_value

        # If no session data found, this might not be an activity file
        if not activity_data["start_date"]:
            return None

        # Generate provider_id from activity start timestamp (stable across copies)
        activity_data["provider_id"] = int(activity_data["start_date"].timestamp())

        # Try to get activity name from file message
        for record in self.fit.get_messages("file_id"):
            for field in record:
                if field.name == "time_created" and not activity_data["name"]:
                    dt_str = field.value.strftime("%Y-%m-%d %H:%M")
                    activity_data["name"] = f"Garmin Activity {dt_str}"

        # Default name if still None
        if not activity_data["name"]:
            dt_str = activity_data["start_date"].strftime("%Y-%m-%d %H:%M")
            activity_data["name"] = f"Garmin Activity {dt_str}"

        return activity_data

    def _normalize_activity_type(self, garmin_sport: str) -> str:
        """Normalize Garmin sport type to standard type.

        Args:
            garmin_sport: Garmin sport type string

        Returns:
            Normalized activity type
        """
        # Map Garmin sport types to standard types
        type_mapping = {
            "running": "Run",
            "cycling": "Ride",
            "swimming": "Swim",
            "walking": "Walk",
            "hiking": "Hike",
            "generic": "Workout",
            "training": "Workout",
            "transition": "Workout",
            "fitness_equipment": "Workout",
            "rowing": "Rowing",
            "stand_up_paddleboarding": "StandUpPaddling",
            "strength_training": "WeightTraining",
            "yoga": "Yoga",
        }

        sport_lower = str(garmin_sport).lower() if garmin_sport else "generic"
        fallback = garmin_sport.capitalize() if garmin_sport else "Workout"
        return type_mapping.get(sport_lower, fallback)


def parse_fit_file(fit_file_path: Path) -> dict | None:
    """Parse a FIT file and return activity data.

    Convenience function for one-off parsing.

    Args:
        fit_file_path: Path to .fit file

    Returns:
        Activity data dictionary or None if parsing failed
    """
    try:
        parser = FitActivityParser(fit_file_path)
        return parser.parse()
    except Exception:
        return None
