"""CSV export for activities."""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openactivity.db.models import Activity

ACTIVITY_COLUMNS = [
    "id",
    "name",
    "type",
    "start_date",
    "distance",
    "moving_time",
    "elapsed_time",
    "total_elevation_gain",
    "average_speed",
    "average_heartrate",
    "max_heartrate",
    "average_watts",
    "calories",
    "gear_id",
]


def activities_to_csv(activities: list[Activity]) -> str:
    """Export a list of activities to CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=ACTIVITY_COLUMNS)
    writer.writeheader()

    for a in activities:
        writer.writerow(
            {
                "id": a.id,
                "name": a.name or "",
                "type": a.type or "",
                "start_date": a.start_date.isoformat() if a.start_date else "",
                "distance": f"{a.distance:.1f}",
                "moving_time": a.moving_time,
                "elapsed_time": a.elapsed_time,
                "total_elevation_gain": f"{a.total_elevation_gain:.1f}",
                "average_speed": f"{a.average_speed:.2f}",
                "average_heartrate": f"{a.average_heartrate:.0f}" if a.average_heartrate else "",
                "max_heartrate": f"{a.max_heartrate:.0f}" if a.max_heartrate else "",
                "average_watts": f"{a.average_watts:.0f}" if a.average_watts else "",
                "calories": f"{a.calories:.0f}" if a.calories else "",
                "gear_id": a.gear_id or "",
            }
        )

    return output.getvalue()
