"""Unit conversion functions for metric/imperial display."""

from __future__ import annotations

METERS_PER_MILE = 1609.344
METERS_PER_FOOT = 0.3048
METERS_PER_KM = 1000.0


def meters_to_display(meters: float, system: str = "metric") -> tuple[float, str]:
    """Convert meters to display distance with unit label."""
    if system == "imperial":
        return meters / METERS_PER_MILE, "mi"
    return meters / METERS_PER_KM, "km"


def format_distance(meters: float, system: str = "metric") -> str:
    """Format distance for display (e.g., '10.2 km' or '6.3 mi')."""
    value, unit = meters_to_display(meters, system)
    return f"{value:.1f} {unit}"


def format_elevation(meters: float, system: str = "metric") -> str:
    """Format elevation for display (e.g., '85 m' or '279 ft')."""
    if system == "imperial":
        return f"{meters / METERS_PER_FOOT:.0f} ft"
    return f"{meters:.0f} m"


def format_speed_as_pace(meters_per_second: float, system: str = "metric") -> str:
    """Convert m/s to pace string (e.g., '4:52 /km' or '7:50 /mi')."""
    if meters_per_second <= 0:
        return "N/A"
    if system == "imperial":
        seconds_per_mile = METERS_PER_MILE / meters_per_second
        minutes = int(seconds_per_mile // 60)
        secs = int(seconds_per_mile % 60)
        return f"{minutes}:{secs:02d} /mi"
    seconds_per_km = METERS_PER_KM / meters_per_second
    minutes = int(seconds_per_km // 60)
    secs = int(seconds_per_km % 60)
    return f"{minutes}:{secs:02d} /km"


def format_speed(meters_per_second: float, system: str = "metric") -> str:
    """Convert m/s to speed string (e.g., '25.3 km/h' or '15.7 mph')."""
    if system == "imperial":
        mph = meters_per_second * 3600 / METERS_PER_MILE
        return f"{mph:.1f} mph"
    kph = meters_per_second * 3600 / METERS_PER_KM
    return f"{kph:.1f} km/h"


def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration (e.g., '1:32:10' or '48:32')."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
