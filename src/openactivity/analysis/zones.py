"""Zone distribution aggregation across activities."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from openactivity.db.models import Activity, ActivityZone

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def compute_zone_distribution(
    session: Session,
    *,
    zone_type: str = "heartrate",
    activity_type: str | None = None,
    last: str = "all",
) -> list[dict]:
    """Aggregate zone time across activities.

    Returns list of dicts with keys: zone_index, min_value, max_value,
    total_seconds, percentage.
    """
    after = _parse_time_window(last)

    query = (
        session.query(ActivityZone)
        .join(Activity, Activity.id == ActivityZone.activity_id)
        .filter(ActivityZone.zone_type == zone_type)
    )

    if activity_type:
        query = query.filter(Activity.type.ilike(activity_type))
    if after:
        query = query.filter(Activity.start_date >= after)

    zones = query.all()

    if not zones:
        return []

    aggregated: dict[int, dict] = defaultdict(
        lambda: {"min_value": 0, "max_value": 0, "total_seconds": 0}
    )

    for z in zones:
        agg = aggregated[z.zone_index]
        agg["min_value"] = z.min_value
        agg["max_value"] = z.max_value
        agg["total_seconds"] += z.time_seconds

    total_time = sum(a["total_seconds"] for a in aggregated.values())

    result = []
    for idx in sorted(aggregated):
        agg = aggregated[idx]
        pct = (agg["total_seconds"] / total_time * 100) if total_time > 0 else 0
        result.append(
            {
                "zone_index": idx,
                "min_value": agg["min_value"],
                "max_value": agg["max_value"],
                "total_seconds": agg["total_seconds"],
                "percentage": round(pct, 1),
            }
        )

    return result


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
