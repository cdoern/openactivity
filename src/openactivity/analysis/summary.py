"""Training volume aggregation."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from openactivity.db.queries import get_activities

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def compute_summary(
    session: Session,
    *,
    period: str = "weekly",
    last: str = "90d",
    activity_type: str | None = None,
    provider: str | None = None,
) -> list[dict]:
    """Aggregate training volume by time period.

    Returns list of dicts with keys: period_start, count, distance,
    moving_time, elevation_gain.
    """
    after = _parse_time_window(last)

    activities = get_activities(
        session,
        activity_type=activity_type,
        after=after,
        provider=provider,
        limit=10000,
        offset=0,
    )

    buckets: dict[str, dict] = defaultdict(
        lambda: {
            "count": 0,
            "distance": 0.0,
            "moving_time": 0,
            "elevation_gain": 0.0,
        }
    )

    for a in activities:
        if not a.start_date:
            continue
        key = _bucket_key(a.start_date, period)
        b = buckets[key]
        b["count"] += 1
        b["distance"] += a.distance
        b["moving_time"] += a.moving_time
        b["elevation_gain"] += a.total_elevation_gain

    result = []
    for key in sorted(buckets):
        entry = {"period_start": key, **buckets[key]}
        result.append(entry)

    return result


def _bucket_key(dt: datetime, period: str) -> str:
    """Return a string key for the time bucket."""
    if period == "daily":
        return dt.strftime("%Y-%m-%d")
    if period == "monthly":
        return dt.strftime("%Y-%m")
    # weekly (default) — ISO week start (Monday)
    monday = dt - timedelta(days=dt.weekday())
    return monday.strftime("%Y-%m-%d")


def _parse_time_window(last: str) -> datetime | None:
    """Parse a time window string like '90d', '6m', '1y' into a datetime."""
    if not last or last == "all":
        return None
    unit = last[-1].lower()
    try:
        value = int(last[:-1])
    except ValueError:
        return None
    now = datetime.now()
    if unit == "d":
        return now - timedelta(days=value)
    if unit == "m":
        return now - timedelta(days=value * 30)
    if unit == "y":
        return now - timedelta(days=value * 365)
    return None
