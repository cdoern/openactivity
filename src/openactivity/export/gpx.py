"""GPX file generation from activity stream data."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import TYPE_CHECKING

import gpxpy
import gpxpy.gpx

if TYPE_CHECKING:
    from openactivity.db.models import Activity, ActivityStream


def generate_gpx(activity: Activity, streams: list[ActivityStream]) -> gpxpy.gpx.GPX:
    """Generate a GPX object from activity data and streams.

    Requires at minimum a 'latlng' stream. Optionally includes
    altitude, heartrate, cadence, and power extensions.
    """
    gpx = gpxpy.gpx.GPX()
    gpx.creator = "openactivity"

    track = gpxpy.gpx.GPXTrack()
    track.name = activity.name or "Activity"
    track.type = activity.type or ""
    gpx.tracks.append(track)

    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)

    # Parse streams into dicts keyed by type
    stream_data: dict[str, list] = {}
    for s in streams:
        try:
            stream_data[s.stream_type] = json.loads(s.data)
        except (json.JSONDecodeError, TypeError):
            continue

    latlng = stream_data.get("latlng")
    if not latlng:
        msg = "No GPS data available for this activity."
        raise ValueError(msg)

    altitude = stream_data.get("altitude", [])
    time_data = stream_data.get("time", [])
    heartrate = stream_data.get("heartrate", [])
    cadence = stream_data.get("cadence", [])
    watts = stream_data.get("watts", [])

    start_time = activity.start_date

    for i, coords in enumerate(latlng):
        try:
            lat, lng = coords[0], coords[1]
        except (IndexError, TypeError):
            continue

        point = gpxpy.gpx.GPXTrackPoint(
            latitude=lat,
            longitude=lng,
            elevation=altitude[i] if i < len(altitude) else None,
        )

        if start_time and i < len(time_data):
            point.time = start_time + timedelta(seconds=time_data[i])

        # Add extensions for HR, cadence, power
        extensions = []
        if i < len(heartrate):
            extensions.append(f"<hr>{heartrate[i]}</hr>")
        if i < len(cadence):
            extensions.append(f"<cad>{cadence[i]}</cad>")
        if i < len(watts):
            extensions.append(f"<power>{watts[i]}</power>")

        if extensions:
            import xml.etree.ElementTree as ET

            ext_elem = ET.fromstring("<extensions>" + "".join(extensions) + "</extensions>")
            point.extensions.append(ext_elem)

        segment.points.append(point)

    return gpx


def gpx_to_string(gpx: gpxpy.gpx.GPX) -> str:
    """Serialize GPX to XML string."""
    return gpx.to_xml()
