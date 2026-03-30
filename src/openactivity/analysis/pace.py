"""Pace trend computation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from openactivity.db.queries import get_activities

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def compute_pace_trend(
    session: Session,
    *,
    last: str = "90d",
    activity_type: str = "Run",
    provider: str | None = None,
) -> dict:
    """Compute average pace per activity over a time window.

    Returns dict with keys: activities (list of {date, pace_per_km}),
    trend ("improving", "declining", "stable"), avg_pace.
    """
    after = _parse_time_window(last)

    activities = get_activities(
        session,
        activity_type=activity_type,
        after=after,
        provider=provider,
        sort="date",
        limit=10000,
        offset=0,
    )

    data_points = []
    for a in activities:
        if not a.start_date or a.distance <= 0 or a.moving_time <= 0:
            continue
        pace_per_km = a.moving_time / (a.distance / 1000.0)
        data_points.append(
            {
                "date": a.start_date.isoformat(),
                "name": a.name,
                "distance": a.distance,
                "pace_per_km": pace_per_km,
            }
        )

    if not data_points:
        return {"activities": [], "trend": "stable", "avg_pace": 0}

    paces = [d["pace_per_km"] for d in data_points]
    avg_pace = sum(paces) / len(paces)

    # Trend: compare first half avg to second half avg
    mid = len(paces) // 2
    if mid > 0:
        first_half = sum(paces[:mid]) / mid
        second_half = sum(paces[mid:]) / (len(paces) - mid)
        diff_pct = (second_half - first_half) / first_half * 100
        if diff_pct < -2:
            trend = "improving"
        elif diff_pct > 2:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    return {
        "activities": data_points,
        "trend": trend,
        "avg_pace": avg_pace,
    }


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
