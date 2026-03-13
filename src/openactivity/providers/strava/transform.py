"""Transform stravalib models to SQLAlchemy model instances."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from openactivity.db.models import (
    Activity,
    ActivityStream,
    ActivityZone,
    Athlete,
    AthleteStats,
    AthleteZone,
    Gear,
    Lap,
    Segment,
    SegmentEffort,
)

if TYPE_CHECKING:
    from stravalib import model as strava_model


def _to_float(val: Any) -> float:
    """Safely convert stravalib quantity types to float."""
    if val is None:
        return 0.0
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _to_int(val: Any) -> int:
    """Safely convert to int."""
    if val is None:
        return 0
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _latlng_to_str(latlng: Any) -> str | None:
    """Convert a LatLon object to 'lat,lng' string."""
    if latlng is None:
        return None
    try:
        return f"{latlng[0]},{latlng[1]}"
    except (IndexError, TypeError):
        return None


def transform_athlete(athlete: strava_model.DetailedAthlete) -> Athlete:
    """Transform a stravalib DetailedAthlete to local Athlete model."""
    return Athlete(
        id=athlete.id,
        username=getattr(athlete, "username", None),
        firstname=athlete.firstname,
        lastname=athlete.lastname,
        city=athlete.city,
        state=athlete.state,
        country=athlete.country,
        measurement_pref=getattr(athlete, "measurement_preference", None),
        weight=_to_float(getattr(athlete, "weight", None)) or None,
        ftp=getattr(athlete, "ftp", None),
    )


def transform_athlete_stats(
    athlete_id: int,
    stats: strava_model.ActivityStats,
) -> list[AthleteStats]:
    """Transform stravalib ActivityStats into AthleteStats rows."""
    rows: list[AthleteStats] = []

    mappings = [
        ("ytd", "run", "ytd_run_totals"),
        ("ytd", "ride", "ytd_ride_totals"),
        ("ytd", "swim", "ytd_swim_totals"),
        ("all_time", "run", "all_run_totals"),
        ("all_time", "ride", "all_ride_totals"),
        ("all_time", "swim", "all_swim_totals"),
        ("recent", "run", "recent_run_totals"),
        ("recent", "ride", "recent_ride_totals"),
        ("recent", "swim", "recent_swim_totals"),
    ]

    for stat_type, activity_type, attr in mappings:
        totals = getattr(stats, attr, None)
        if totals is None:
            continue
        rows.append(
            AthleteStats(
                athlete_id=athlete_id,
                stat_type=stat_type,
                activity_type=activity_type,
                count=_to_int(totals.count),
                distance=_to_float(totals.distance),
                moving_time=_to_int(totals.moving_time),
                elapsed_time=_to_int(totals.elapsed_time),
                elevation_gain=_to_float(totals.elevation_gain),
            )
        )

    return rows


def transform_activity(
    activity: strava_model.SummaryActivity | strava_model.DetailedActivity,
    athlete_id: int,
) -> Activity:
    """Transform a stravalib activity to local Activity model."""
    return Activity(
        id=activity.id,
        athlete_id=athlete_id,
        name=activity.name,
        type=str(activity.type) if activity.type else None,
        sport_type=str(activity.sport_type) if activity.sport_type else None,
        start_date=activity.start_date,
        start_date_local=activity.start_date_local,
        timezone=str(activity.timezone) if activity.timezone else None,
        distance=_to_float(activity.distance),
        moving_time=_to_int(activity.moving_time),
        elapsed_time=_to_int(activity.elapsed_time),
        total_elevation_gain=_to_float(activity.total_elevation_gain),
        average_speed=_to_float(activity.average_speed),
        max_speed=_to_float(activity.max_speed),
        average_heartrate=_to_float(getattr(activity, "average_heartrate", None)) or None,
        max_heartrate=_to_float(getattr(activity, "max_heartrate", None)) or None,
        average_cadence=_to_float(getattr(activity, "average_cadence", None)) or None,
        average_watts=_to_float(getattr(activity, "average_watts", None)) or None,
        weighted_average_watts=_to_float(getattr(activity, "weighted_average_watts", None)) or None,
        max_watts=_to_int(getattr(activity, "max_watts", None)) or None,
        kilojoules=_to_float(getattr(activity, "kilojoules", None)) or None,
        calories=_to_float(getattr(activity, "calories", None)) or None,
        suffer_score=_to_int(getattr(activity, "suffer_score", None)) or None,
        gear_id=getattr(getattr(activity, "gear", None), "id", None)
        if hasattr(activity, "gear")
        else activity.gear_id
        if hasattr(activity, "gear_id")
        else None,
        description=getattr(activity, "description", None),
        has_heartrate=bool(getattr(activity, "has_heartrate", False)),
        has_power=bool(getattr(activity, "device_watts", False)),
        start_latlng=_latlng_to_str(activity.start_latlng),
        end_latlng=_latlng_to_str(activity.end_latlng),
        synced_detail=False,
    )


def transform_laps(
    laps: list[strava_model.Lap],
    activity_id: int,
) -> list[Lap]:
    """Transform stravalib laps to local Lap models."""
    result = []
    for lap in laps:
        result.append(
            Lap(
                id=lap.id,
                activity_id=activity_id,
                lap_index=_to_int(lap.lap_index),
                name=lap.name,
                distance=_to_float(lap.distance),
                moving_time=_to_int(lap.moving_time),
                elapsed_time=_to_int(lap.elapsed_time),
                total_elevation_gain=_to_float(lap.total_elevation_gain),
                average_speed=_to_float(lap.average_speed),
                max_speed=_to_float(lap.max_speed),
                average_heartrate=_to_float(getattr(lap, "average_heartrate", None)) or None,
                max_heartrate=_to_float(getattr(lap, "max_heartrate", None)) or None,
                average_cadence=_to_float(getattr(lap, "average_cadence", None)) or None,
                average_watts=_to_float(getattr(lap, "average_watts", None)) or None,
                start_index=_to_int(lap.start_index),
                end_index=_to_int(lap.end_index),
            )
        )
    return result


def transform_activity_zones(
    zones: list[strava_model.ActivityZone],
    activity_id: int,
) -> list[ActivityZone]:
    """Transform stravalib ActivityZone list to local models."""
    result = []
    for zone in zones:
        zone_type = str(zone.type) if zone.type else "heartrate"
        buckets = zone.distribution_buckets
        if not buckets:
            continue
        for idx, bucket in enumerate(buckets):
            result.append(
                ActivityZone(
                    activity_id=activity_id,
                    zone_type=zone_type,
                    zone_index=idx + 1,
                    min_value=_to_int(bucket.min),
                    max_value=_to_int(bucket.max),
                    time_seconds=_to_int(bucket.time),
                )
            )
    return result


def transform_athlete_zones(
    zones: list,
    athlete_id: int,
) -> list[AthleteZone]:
    """Transform stravalib athlete zones to local models."""
    result = []
    for zone in zones:
        zone_type = getattr(zone, "type", "heartrate")
        zone_ranges = getattr(zone, "zones", [])
        for idx, z in enumerate(zone_ranges):
            result.append(
                AthleteZone(
                    athlete_id=athlete_id,
                    zone_type=str(zone_type),
                    zone_index=idx + 1,
                    min_value=_to_int(getattr(z, "min", 0)),
                    max_value=_to_int(getattr(z, "max", -1)),
                )
            )
    return result


def transform_streams(
    streams: dict[str, strava_model.Stream],
    activity_id: int,
) -> list[ActivityStream]:
    """Transform stravalib stream data to local models."""
    result = []
    for stream_type, stream in streams.items():
        data = list(stream.data) if stream.data else []
        result.append(
            ActivityStream(
                activity_id=activity_id,
                stream_type=str(stream_type),
                data=json.dumps(data).encode("utf-8"),
                resolution=stream.resolution or "high",
            )
        )
    return result


def transform_gear(
    gear: strava_model.SummaryGear | strava_model.DetailedGear,
) -> Gear:
    """Transform stravalib gear to local Gear model."""
    return Gear(
        id=gear.id,
        name=gear.name,
        distance=_to_float(gear.distance),
        brand_name=getattr(gear, "brand_name", None),
        model_name=getattr(gear, "model_name", None),
        gear_type=getattr(gear, "frame_type", None) and "bike" or "shoes",
    )


def transform_segment(
    segment: strava_model.SummarySegment | strava_model.DetailedSegment,
) -> Segment:
    """Transform stravalib segment to local Segment model."""
    return Segment(
        id=segment.id,
        name=segment.name,
        activity_type=str(segment.activity_type) if segment.activity_type else None,
        distance=_to_float(segment.distance),
        average_grade=_to_float(segment.average_grade),
        maximum_grade=_to_float(segment.maximum_grade),
        elevation_high=_to_float(segment.elevation_high),
        elevation_low=_to_float(segment.elevation_low),
        total_elevation_gain=_to_float(getattr(segment, "total_elevation_gain", 0)),
        starred=bool(getattr(segment, "starred", False)),
        pr_time=_to_int(
            getattr(
                getattr(segment, "athlete_pr_effort", None),
                "elapsed_time",
                None,
            )
        )
        or None,
        effort_count=_to_int(
            getattr(segment, "athlete_segment_stats", None)
            and getattr(segment.athlete_segment_stats, "effort_count", 0)
        ),
    )


def transform_segment_effort(
    effort: strava_model.SegmentEffort,
) -> SegmentEffort:
    """Transform stravalib segment effort to local model."""
    return SegmentEffort(
        id=effort.id,
        segment_id=effort.segment.id if effort.segment else 0,
        activity_id=effort.activity.id if effort.activity else 0,
        elapsed_time=_to_int(effort.elapsed_time),
        moving_time=_to_int(effort.moving_time),
        start_date=effort.start_date,
        pr_rank=getattr(effort, "pr_rank", None),
        average_heartrate=_to_float(getattr(effort, "average_heartrate", None)) or None,
        average_watts=_to_float(getattr(effort, "average_watts", None)) or None,
    )
