"""Transform Garmin Connect API data to local database models."""

from __future__ import annotations

from datetime import datetime


def transform_activity(garmin_activity: dict) -> dict:
    """Transform Garmin activity to local Activity model format.

    Args:
        garmin_activity: Raw activity dictionary from Garmin Connect API

    Returns:
        Dictionary with fields matching Activity model schema
    """
    # Extract activity ID
    activity_id = garmin_activity.get("activityId")

    # Parse start date (Garmin uses different datetime format)
    start_date_str = garmin_activity.get("startTimeGMT") or garmin_activity.get("beginTimestamp")
    start_date = None
    if start_date_str:
        try:
            # Try ISO format first
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

    start_date_local_str = garmin_activity.get("startTimeLocal")
    start_date_local = None
    if start_date_local_str:
        try:
            start_date_local = datetime.fromisoformat(start_date_local_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

    # Extract metrics
    distance = garmin_activity.get("distance", 0.0)  # meters
    elapsed_time = garmin_activity.get("elapsedDuration", 0)  # seconds
    moving_time = garmin_activity.get("movingDuration", elapsed_time)  # seconds
    elevation_gain = garmin_activity.get("elevationGain", 0.0)  # meters

    # Speed calculations
    avg_speed = garmin_activity.get("averageSpeed", 0.0)  # m/s
    max_speed = garmin_activity.get("maxSpeed", 0.0)  # m/s

    # Heart rate
    avg_hr = garmin_activity.get("averageHR")
    max_hr = garmin_activity.get("maxHR")
    has_heartrate = avg_hr is not None

    # Power data (if available)
    avg_power = garmin_activity.get("avgPower")
    max_power = garmin_activity.get("maxPower")
    has_power = avg_power is not None

    # Calories
    calories = garmin_activity.get("calories")

    # Activity type normalization
    activity_type = garmin_activity.get("activityType", {}).get("typeKey", "")
    sport_type = normalize_activity_type(activity_type)

    return {
        "id": None,  # Will be assigned by database
        "provider": "garmin",
        "provider_id": activity_id,
        "athlete_id": 1,  # TODO: Handle multi-athlete support
        "name": garmin_activity.get("activityName", "Untitled"),
        "type": sport_type,
        "sport_type": activity_type,
        "start_date": start_date,
        "start_date_local": start_date_local,
        "timezone": None,  # Garmin doesn't always provide this
        "distance": distance,
        "moving_time": moving_time,
        "elapsed_time": elapsed_time,
        "total_elevation_gain": elevation_gain,
        "average_speed": avg_speed,
        "max_speed": max_speed,
        "average_heartrate": avg_hr,
        "max_heartrate": max_hr,
        "average_cadence": garmin_activity.get("avgRunCadence") or garmin_activity.get("avgBikeCadence"),
        "average_watts": avg_power,
        "weighted_average_watts": None,  # Not provided by Garmin
        "max_watts": max_power,
        "kilojoules": None,  # Calculate if needed
        "calories": calories,
        "suffer_score": None,  # Strava-specific
        "gear_id": None,  # Not easily mapped from Garmin
        "description": garmin_activity.get("description"),
        "has_heartrate": has_heartrate,
        "has_power": has_power,
        "start_latlng": None,  # TODO: Extract from location if available
        "end_latlng": None,
        "synced_detail": False,  # Mark as basic sync
        "pr_scanned": False,
    }


def normalize_activity_type(garmin_type: str) -> str:
    """Normalize Garmin activity type to standard type.

    Args:
        garmin_type: Garmin activity type key (e.g., "running", "cycling")

    Returns:
        Normalized activity type (e.g., "Run", "Ride")
    """
    # Map common Garmin types to Strava-like types for consistency
    type_mapping = {
        "running": "Run",
        "trail_running": "Run",
        "treadmill_running": "Run",
        "cycling": "Ride",
        "road_biking": "Ride",
        "mountain_biking": "Ride",
        "virtual_ride": "VirtualRide",
        "indoor_cycling": "VirtualRide",
        "swimming": "Swim",
        "open_water_swimming": "Swim",
        "walking": "Walk",
        "hiking": "Hike",
        "strength_training": "WeightTraining",
        "yoga": "Yoga",
    }

    return type_mapping.get(garmin_type.lower(), garmin_type.capitalize())


def transform_daily_summary(date: str, stats: dict, hrv_data: dict | None, body_battery: list[dict] | None) -> dict:
    """Transform Garmin daily stats to GarminDailySummary model format.

    Args:
        date: Date string in YYYY-MM-DD format
        stats: Daily stats dictionary from Garmin API
        hrv_data: HRV data dictionary (optional)
        body_battery: Body Battery data list (optional)

    Returns:
        Dictionary with fields matching GarminDailySummary model
    """
    # Extract resting HR
    resting_hr = stats.get("restingHeartRate")

    # Extract HRV average
    hrv_avg = None
    if hrv_data and isinstance(hrv_data, dict):
        hrv_values = hrv_data.get("hrvValues")
        if hrv_values and len(hrv_values) > 0:
            hrv_avg = int(sum(v.get("value", 0) for v in hrv_values) / len(hrv_values))

    # Extract Body Battery min/max
    bb_min = None
    bb_max = None
    if body_battery and isinstance(body_battery, list):
        values = [point.get("value") for point in body_battery if point.get("value") is not None]
        if values:
            bb_min = min(values)
            bb_max = max(values)

    # Extract stress average
    stress_avg = stats.get("averageStressLevel")

    # Extract steps
    steps = stats.get("totalSteps")

    # Extract respiration
    respiration_avg = stats.get("avgWakingRespirationValue")

    # Extract SpO2
    spo2_avg = stats.get("avgSleepSpo2")

    return {
        "date": datetime.strptime(date, "%Y-%m-%d").date(),
        "resting_hr": resting_hr,
        "hrv_avg": hrv_avg,
        "body_battery_max": bb_max,
        "body_battery_min": bb_min,
        "stress_avg": stress_avg,
        "sleep_score": None,  # Will be populated from sleep data
        "steps": steps,
        "respiration_avg": respiration_avg,
        "spo2_avg": spo2_avg,
    }


def transform_sleep_session(date: str, sleep_data: dict) -> dict | None:
    """Transform Garmin sleep data to GarminSleepSession model format.

    Args:
        date: Date string in YYYY-MM-DD format
        sleep_data: Sleep data dictionary from Garmin API

    Returns:
        Dictionary with fields matching GarminSleepSession model, or None if no valid data
    """
    if not sleep_data:
        return None

    # Extract sleep times
    start_time_str = sleep_data.get("sleepStartTimestampGMT")
    end_time_str = sleep_data.get("sleepEndTimestampGMT")

    if not start_time_str or not end_time_str:
        return None

    try:
        start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None

    # Extract durations (in seconds)
    total_duration = sleep_data.get("sleepTimeSeconds", 0)
    deep_duration = sleep_data.get("deepSleepSeconds")
    light_duration = sleep_data.get("lightSleepSeconds")
    rem_duration = sleep_data.get("remSleepSeconds")
    awake_duration = sleep_data.get("awakeSleepSeconds")

    # Sleep score
    sleep_score = sleep_data.get("sleepScores", {}).get("overall", {}).get("value")

    return {
        "date": datetime.strptime(date, "%Y-%m-%d").date(),
        "start_time": start_time,
        "end_time": end_time,
        "total_duration_seconds": total_duration,
        "deep_duration_seconds": deep_duration,
        "light_duration_seconds": light_duration,
        "rem_duration_seconds": rem_duration,
        "awake_duration_seconds": awake_duration,
        "sleep_score": sleep_score,
    }
