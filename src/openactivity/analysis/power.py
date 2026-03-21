"""Power curve computation from stream data."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from openactivity.db.models import Activity, ActivityStream

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Key durations in seconds
DURATIONS = [
    (5, "5s"),
    (60, "1min"),
    (300, "5min"),
    (1200, "20min"),
    (3600, "60min"),
]


def compute_power_curve(
    session: Session,
    *,
    last: str = "90d",
) -> list[dict]:
    """Compute best average power for key durations.

    Returns list of dicts with keys: duration_label, duration_seconds,
    best_power, date, activity_name.
    """
    after = _parse_time_window(last)

    query = (
        session.query(ActivityStream, Activity)
        .join(Activity, Activity.id == ActivityStream.activity_id)
        .filter(ActivityStream.stream_type == "watts")
    )
    if after:
        query = query.filter(Activity.start_date >= after)

    rows = query.all()

    results = []
    for duration_secs, label in DURATIONS:
        best = _find_best_power(rows, duration_secs)
        results.append(
            {
                "duration_label": label,
                "duration_seconds": duration_secs,
                "best_power": best["power"] if best else None,
                "date": best["date"] if best else None,
                "activity_name": best["name"] if best else None,
            }
        )

    return results


def _find_best_power(rows: list, duration_secs: int) -> dict | None:
    """Find the best average power for a given duration across activities."""
    best: dict | None = None

    for stream, activity in rows:
        try:
            data = json.loads(stream.data)
        except (json.JSONDecodeError, TypeError):
            continue

        if len(data) < duration_secs:
            continue

        # Sliding window for best average
        window_sum = sum(data[:duration_secs])
        max_avg = window_sum / duration_secs

        for i in range(1, len(data) - duration_secs + 1):
            window_sum += data[i + duration_secs - 1] - data[i - 1]
            avg = window_sum / duration_secs
            if avg > max_avg:
                max_avg = avg

        if best is None or max_avg > best["power"]:
            best = {
                "power": round(max_avg),
                "date": activity.start_date.isoformat() if activity.start_date else None,
                "name": activity.name,
            }

    return best


def _parse_time_window(last: str) -> datetime | None:
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
