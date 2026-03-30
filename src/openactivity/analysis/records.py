"""Personal records scanning and management."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from openactivity.db.models import (
    Activity,
    ActivityStream,
    CustomDistance,
    PersonalRecord,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Standard running distances: (label, meters)
RUNNING_DISTANCES: list[tuple[str, float]] = [
    ("1mi", 1609.344),
    ("5K", 5000.0),
    ("10K", 10000.0),
    ("half", 21097.5),
    ("marathon", 42195.0),
]

# Standard cycling power durations: (label, seconds)
CYCLING_POWER_DURATIONS: list[tuple[str, int]] = [
    ("5s", 5),
    ("1min", 60),
    ("5min", 300),
    ("20min", 1200),
    ("60min", 3600),
]

# All standard labels for validation
STANDARD_LABELS: set[str] = {label for label, _ in RUNNING_DISTANCES} | {
    label for label, _ in CYCLING_POWER_DURATIONS
}

# Display-friendly names
DISTANCE_DISPLAY: dict[str, str] = {
    "1mi": "1 mile",
    "5K": "5K",
    "10K": "10K",
    "half": "Half Marathon",
    "marathon": "Marathon",
    "5s": "5 seconds",
    "1min": "1 minute",
    "5min": "5 minutes",
    "20min": "20 minutes",
    "60min": "60 minutes",
}

# Sort order: shortest distance/duration first
SORT_ORDER: dict[str, int] = {
    "1mi": 0, "5K": 1, "10K": 2, "half": 3, "marathon": 4,
    "5s": 0, "1min": 1, "5min": 2, "20min": 3, "60min": 4,
}


def sort_records(records: list) -> list:
    """Sort records by canonical distance/duration order."""
    return sorted(
        records,
        key=lambda r: SORT_ORDER.get(
            r.distance_type if hasattr(r, "distance_type") else r.get("distance_type", ""),
            99,
        ),
    )


def find_best_effort_for_distance(
    distance_stream: list[float],
    time_stream: list[float],
    target_meters: float,
) -> float | None:
    """Find fastest time for a target distance using sliding window.

    Args:
        distance_stream: Cumulative distance in meters.
        time_stream: Cumulative elapsed time in seconds.
        target_meters: Target distance to find best effort for.

    Returns:
        Best time in seconds, or None if distance not covered.
    """
    if not distance_stream or not time_stream:
        return None
    if len(distance_stream) != len(time_stream):
        return None
    if distance_stream[-1] < target_meters:
        return None

    best_time: float | None = None
    start = 0

    for end in range(len(distance_stream)):
        while distance_stream[end] - distance_stream[start] >= target_meters:
            elapsed = time_stream[end] - time_stream[start]
            if best_time is None or elapsed < best_time:
                best_time = elapsed
            start += 1

    return best_time


def find_best_power_for_duration(
    watts_stream: list[float],
    target_seconds: int,
) -> float | None:
    """Find best average power for a target duration using sliding window.

    Args:
        watts_stream: Instantaneous watts readings (1-second resolution).
        target_seconds: Duration in seconds.

    Returns:
        Best average power in watts, or None if stream too short.
    """
    if not watts_stream or len(watts_stream) < target_seconds:
        return None

    window_sum = sum(watts_stream[:target_seconds])
    max_avg = window_sum / target_seconds

    for i in range(1, len(watts_stream) - target_seconds + 1):
        window_sum += watts_stream[i + target_seconds - 1] - watts_stream[i - 1]
        avg = window_sum / target_seconds
        if avg > max_avg:
            max_avg = avg

    return round(max_avg)


def _get_all_distances(session: Session) -> list[tuple[str, float]]:
    """Get all distances (standard + custom) for scanning."""
    distances = list(RUNNING_DISTANCES)
    custom = session.query(CustomDistance).all()
    for cd in custom:
        distances.append((cd.label, cd.distance_meters))
    return distances


def _update_record(
    session: Session,
    record_type: str,
    distance_type: str,
    value: float,
    activity: Activity,
    *,
    pace: float | None = None,
    distance_meters: float | None = None,
    duration_seconds: int | None = None,
) -> bool:
    """Insert or update a personal record. Returns True if new/updated PR."""
    current = (
        session.query(PersonalRecord)
        .filter(
            PersonalRecord.distance_type == distance_type,
            PersonalRecord.is_current.is_(True),
        )
        .first()
    )

    if record_type == "distance":
        is_better = current is None or value < current.value
    else:
        is_better = current is None or value > current.value

    if not is_better:
        return False

    if current is not None:
        current.is_current = False

    new_record = PersonalRecord(
        record_type=record_type,
        distance_type=distance_type,
        value=value,
        pace=pace,
        activity_id=activity.id,
        activity_name=activity.name,
        achieved_date=activity.start_date,
        is_current=True,
        distance_meters=distance_meters,
        duration_seconds=duration_seconds,
    )
    session.add(new_record)
    return True


def scan_activity_for_records(
    session: Session,
    activity: Activity,
    distances: list[tuple[str, float]],
) -> dict[str, int]:
    """Scan a single activity for personal records.

    Returns dict with 'new_records' and 'updated_records' counts.
    """
    result = {"new_records": 0, "updated_records": 0}

    streams = (
        session.query(ActivityStream)
        .filter(ActivityStream.activity_id == activity.id)
        .all()
    )

    stream_map: dict[str, list] = {}
    for s in streams:
        try:
            stream_map[s.stream_type] = json.loads(s.data)
        except (json.JSONDecodeError, TypeError):
            continue

    # Distance-based PRs (running activities only)
    raw_type = activity.type or ""
    # Handle stravalib enum format: "root='Run'" or plain "Run"
    if "=" in raw_type:
        activity_type = raw_type.split("=")[-1].strip("'\"").lower()
    else:
        activity_type = raw_type.lower()
    is_run = activity_type == "run"
    is_ride = activity_type == "ride"

    distance_data = stream_map.get("distance")
    time_data = stream_map.get("time")

    if is_run and distance_data and time_data:
        for label, target_meters in distances:
            best_time = find_best_effort_for_distance(
                distance_data, time_data, target_meters
            )
            if best_time is not None and best_time > 0:
                pace = best_time / target_meters
                had_current = (
                    session.query(PersonalRecord)
                    .filter(
                        PersonalRecord.distance_type == label,
                        PersonalRecord.is_current.is_(True),
                    )
                    .first()
                    is not None
                )
                if _update_record(
                    session,
                    "distance",
                    label,
                    best_time,
                    activity,
                    pace=pace,
                    distance_meters=target_meters,
                ):
                    if had_current:
                        result["updated_records"] += 1
                    else:
                        result["new_records"] += 1

    # Power-based PRs (cycling activities only)
    watts_data = stream_map.get("watts")
    if is_ride and watts_data:
        for label, target_seconds in CYCLING_POWER_DURATIONS:
            best_power = find_best_power_for_duration(watts_data, target_seconds)
            if best_power is not None and best_power > 0:
                had_current = (
                    session.query(PersonalRecord)
                    .filter(
                        PersonalRecord.distance_type == label,
                        PersonalRecord.is_current.is_(True),
                    )
                    .first()
                    is not None
                )
                if _update_record(
                    session,
                    "power",
                    label,
                    best_power,
                    activity,
                    duration_seconds=target_seconds,
                ):
                    if had_current:
                        result["updated_records"] += 1
                    else:
                        result["new_records"] += 1

    return result


def scan_all_activities(
    session: Session, *, full: bool = False, provider: str | None = None
) -> dict[str, int]:
    """Scan all activities for personal records.

    Args:
        session: Database session.
        full: If True, reset scan state and re-scan everything.

    Returns:
        Dict with 'scanned', 'new_records', 'updated_records' counts.
    """
    if full:
        session.query(Activity).update({Activity.pr_scanned: False})
        session.query(PersonalRecord).delete()
        session.flush()

    query = session.query(Activity).filter(Activity.pr_scanned.is_(False))
    if provider:
        query = query.filter(Activity.provider == provider)
    activities = query.order_by(Activity.start_date).all()

    distances = _get_all_distances(session)
    totals = {"scanned": 0, "new_records": 0, "updated_records": 0}

    for activity in activities:
        result = scan_activity_for_records(session, activity, distances)
        activity.pr_scanned = True
        totals["scanned"] += 1
        totals["new_records"] += result["new_records"]
        totals["updated_records"] += result["updated_records"]

    session.commit()
    return totals


def add_custom_distance(session: Session, label: str, meters: float) -> CustomDistance:
    """Add a custom distance for PR tracking."""
    if label in STANDARD_LABELS:
        msg = f"'{label}' is a standard distance and cannot be added as custom."
        raise ValueError(msg)

    existing = session.query(CustomDistance).filter_by(label=label).first()
    if existing:
        msg = f"Custom distance '{label}' already exists."
        raise ValueError(msg)

    cd = CustomDistance(label=label, distance_meters=meters)
    session.add(cd)
    # Reset scan state so the next scan evaluates existing activities for this distance
    session.query(Activity).update({Activity.pr_scanned: False})
    session.commit()
    return cd


def remove_custom_distance(session: Session, label: str) -> int:
    """Remove a custom distance and its associated records.

    Returns the number of records removed.
    """
    if label in STANDARD_LABELS:
        msg = f"Cannot remove standard distance '{label}'. Only custom distances can be removed."
        raise ValueError(msg)

    cd = session.query(CustomDistance).filter_by(label=label).first()
    if cd is None:
        msg = f"Custom distance '{label}' not found."
        raise ValueError(msg)

    record_count = (
        session.query(PersonalRecord)
        .filter(PersonalRecord.distance_type == label)
        .delete()
    )
    session.delete(cd)
    session.commit()
    return record_count
