"""Custom time-range comparison analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING

from openactivity.db.queries import get_activities

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


PACE_TYPES = {"Run", "Walk", "Hike", "Trail Run", "VirtualRun"}
SPEED_TYPES = {"Ride", "VirtualRide", "EBikeRide", "Handcycle", "Velomobile"}


@dataclass
class RangeMetrics:
    """Aggregated metrics for a single date range."""

    start_date: date
    end_date: date
    count: int = 0
    distance: float = 0.0
    moving_time: int = 0
    elevation_gain: float = 0.0
    avg_pace: float | None = None  # seconds per meter (foot-based types)
    avg_speed: float | None = None  # m/s (cycling types)
    avg_heartrate: float | None = None


@dataclass
class RangeComparison:
    """Complete comparison result between two date ranges."""

    range1: RangeMetrics
    range2: RangeMetrics
    deltas: dict = field(default_factory=dict)
    pct_changes: dict = field(default_factory=dict)
    activity_type: str | None = None
    overlap: bool = False


def parse_date_range(range_str: str) -> tuple[date, date]:
    """Parse 'YYYY-MM-DD:YYYY-MM-DD' into (start, end) dates.

    Raises ValueError on invalid format or start > end.
    """
    parts = range_str.split(":")
    if len(parts) != 2:
        msg = f"Invalid date range format: '{range_str}'. Expected YYYY-MM-DD:YYYY-MM-DD."
        raise ValueError(msg)

    try:
        start = date.fromisoformat(parts[0].strip())
        end = date.fromisoformat(parts[1].strip())
    except ValueError:
        msg = f"Invalid date format in '{range_str}'. Expected YYYY-MM-DD:YYYY-MM-DD."
        raise ValueError(msg) from None

    if start > end:
        msg = f"Invalid range: start date {start} must be before or equal to end date {end}."
        raise ValueError(msg)

    return start, end


def detect_overlap(
    range1: tuple[date, date], range2: tuple[date, date]
) -> bool:
    """Return True if two date ranges share any dates."""
    return range1[0] <= range2[1] and range2[0] <= range1[1]


def aggregate_range_metrics(
    session: Session,
    *,
    start: date,
    end: date,
    activity_type: str | None = None,
) -> RangeMetrics:
    """Query activities in a date range and compute aggregated metrics."""
    after = datetime(start.year, start.month, start.day)
    before = datetime(end.year, end.month, end.day, 23, 59, 59)

    activities = get_activities(
        session,
        activity_type=activity_type,
        after=after,
        before=before,
        limit=50000,
        offset=0,
    )

    metrics = RangeMetrics(start_date=start, end_date=end)
    metrics.count = len(activities)

    if not activities:
        return metrics

    total_distance = 0.0
    total_moving_time = 0
    total_elevation = 0.0
    hr_sum = 0.0
    hr_count = 0
    pace_sum = 0.0
    pace_count = 0
    speed_sum = 0.0
    speed_count = 0

    for act in activities:
        total_distance += act.distance or 0.0
        total_moving_time += act.moving_time or 0
        total_elevation += act.total_elevation_gain or 0.0

        if act.has_heartrate and act.average_heartrate is not None:
            hr_sum += act.average_heartrate
            hr_count += 1

        act_type = act.type or ""
        avg_speed = act.average_speed or 0.0

        if act_type in PACE_TYPES and avg_speed > 0:
            pace_sum += 1.0 / avg_speed  # seconds per meter
            pace_count += 1
        elif act_type in SPEED_TYPES and avg_speed > 0:
            speed_sum += avg_speed
            speed_count += 1

    metrics.distance = total_distance
    metrics.moving_time = total_moving_time
    metrics.elevation_gain = total_elevation

    if hr_count > 0:
        metrics.avg_heartrate = hr_sum / hr_count

    if pace_count > 0:
        metrics.avg_pace = pace_sum / pace_count

    if speed_count > 0:
        metrics.avg_speed = speed_sum / speed_count

    return metrics


def compute_comparison(
    range1: RangeMetrics,
    range2: RangeMetrics,
    *,
    activity_type: str | None = None,
    overlap: bool = False,
) -> RangeComparison:
    """Compute deltas and percentage changes between two range metrics."""
    metric_keys = [
        ("count", range1.count, range2.count),
        ("distance_m", range1.distance, range2.distance),
        ("moving_time_s", range1.moving_time, range2.moving_time),
        ("elevation_gain_m", range1.elevation_gain, range2.elevation_gain),
    ]

    if range1.avg_pace is not None or range2.avg_pace is not None:
        # Convert sec/meter to sec/km for display
        p1 = (range1.avg_pace or 0.0) * 1000.0 if range1.avg_pace else None
        p2 = (range2.avg_pace or 0.0) * 1000.0 if range2.avg_pace else None
        metric_keys.append(("avg_pace_s_per_km", p1, p2))

    if range1.avg_speed is not None or range2.avg_speed is not None:
        metric_keys.append(("avg_speed_m_s", range1.avg_speed, range2.avg_speed))

    if range1.avg_heartrate is not None or range2.avg_heartrate is not None:
        metric_keys.append(("avg_heartrate", range1.avg_heartrate, range2.avg_heartrate))

    deltas: dict = {}
    pct_changes: dict = {}

    for key, v1, v2 in metric_keys:
        val1 = v1 if v1 is not None else 0.0
        val2 = v2 if v2 is not None else 0.0
        delta = val2 - val1
        deltas[key] = delta

        if val1 != 0:
            pct_changes[key] = (delta / val1) * 100.0
        elif val2 != 0:
            pct_changes[key] = None  # "N/A" — can't compute from zero base
        else:
            pct_changes[key] = 0.0  # both zero

    return RangeComparison(
        range1=range1,
        range2=range2,
        deltas=deltas,
        pct_changes=pct_changes,
        activity_type=activity_type,
        overlap=overlap,
    )


def format_pct_change(value: float | None) -> str:
    """Format a percentage change for table display."""
    if value is None:
        return "N/A"
    if value == 0.0:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%"


def comparison_to_dict(
    comparison: RangeComparison,
    *,
    units: str = "metric",
) -> dict:
    """Serialize a RangeComparison to a dict matching the JSON contract schema."""

    def _range_to_dict(r: RangeMetrics) -> dict:
        d: dict = {
            "count": r.count,
            "distance_m": r.distance,
            "moving_time_s": r.moving_time,
            "elevation_gain_m": r.elevation_gain,
        }
        if r.avg_pace is not None:
            d["avg_pace_s_per_km"] = r.avg_pace * 1000.0
        if r.avg_speed is not None:
            d["avg_speed_m_s"] = r.avg_speed
        if r.avg_heartrate is not None:
            d["avg_heartrate"] = r.avg_heartrate
        return d

    return {
        "metadata": {
            "range1": {
                "start": comparison.range1.start_date.isoformat(),
                "end": comparison.range1.end_date.isoformat(),
            },
            "range2": {
                "start": comparison.range2.start_date.isoformat(),
                "end": comparison.range2.end_date.isoformat(),
            },
            "activity_type": comparison.activity_type,
            "units": units,
            "overlap": comparison.overlap,
        },
        "range1": _range_to_dict(comparison.range1),
        "range2": _range_to_dict(comparison.range2),
        "deltas": comparison.deltas,
        "pct_changes": {
            k: v for k, v in comparison.pct_changes.items()
        },
    }
