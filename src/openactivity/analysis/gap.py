"""Grade-Adjusted Pace (GAP) and Effort Score computation.

Uses the Minetti (2002) energy cost model to compute equivalent flat pace
from elevation and distance stream data. Provides effort scoring based on
duration, GAP, heart rate, and elevation gain.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from openactivity.db.queries import get_activities, get_activity_streams, get_laps

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from openactivity.db.models import Activity, Lap

# Minetti (2002) polynomial coefficients for metabolic cost C(g) in J/kg/m
# C(g) = 155.4g^5 - 30.4g^4 - 43.3g^3 + 46.3g^2 + 19.5g + 3.6
MINETTI_COEFFICIENTS = (155.4, -30.4, -43.3, 46.3, 19.5, 3.6)

# Cost of running on flat ground (grade=0): C(0) = 3.6 J/kg/m
FLAT_COST = 3.6

# Rolling average window size for grade smoothing
SMOOTHING_WINDOW = 10

# Minimum stream data points for reliable GAP computation
MIN_STREAM_POINTS = 10


@dataclass
class GAPResult:
    """Result of GAP computation for a single activity."""

    overall_gap: float | None  # Grade-adjusted pace in m/s (None if unavailable)
    lap_gaps: list[float | None]  # Per-lap GAP in m/s
    grade_profile: list[float]  # Smoothed grade values
    available: bool  # Whether GAP could be computed


@dataclass
class EffortScoreResult:
    """Result of effort scoring for a single activity."""

    score: int  # 0-100 composite effort score
    duration_component: float
    gap_component: float
    hr_component: float | None
    elevation_component: float


def minetti_cost(grade: float) -> float:
    """Compute metabolic cost of running at a given grade using the Minetti model.

    Args:
        grade: Grade as a decimal (e.g., 0.10 = 10% grade).

    Returns:
        Metabolic cost in J/kg/m. Clamped to minimum of 1.0 to avoid
        negative/zero costs at extreme downhill grades.
    """
    c5, c4, c3, c2, c1, c0 = MINETTI_COEFFICIENTS
    cost = (
        c5 * grade**5
        + c4 * grade**4
        + c3 * grade**3
        + c2 * grade**2
        + c1 * grade
        + c0
    )
    # Clamp to minimum to avoid division issues at extreme downhill
    return max(cost, 1.0)


def compute_grades(
    altitude_stream: list[float], distance_stream: list[float]
) -> list[float]:
    """Compute smoothed grade values from altitude and distance streams.

    Grade = (elevation change) / (distance change) between consecutive points,
    smoothed with a rolling average window.

    Args:
        altitude_stream: Altitude values in meters.
        distance_stream: Cumulative distance values in meters.

    Returns:
        List of smoothed grade values (as decimals, e.g., 0.05 = 5%).
    """
    n = min(len(altitude_stream), len(distance_stream))
    if n < 2:
        return []

    # Compute raw grades
    raw_grades: list[float] = []
    for i in range(n - 1):
        dz = altitude_stream[i + 1] - altitude_stream[i]
        dd = distance_stream[i + 1] - distance_stream[i]
        if dd > 0:
            grade = dz / dd
            # Clamp extreme grades to ±1.0 (100%)
            grade = max(-1.0, min(1.0, grade))
            raw_grades.append(grade)
        else:
            # No distance change — assume flat
            raw_grades.append(0.0)

    if not raw_grades:
        return []

    # Apply rolling average smoothing
    smoothed: list[float] = []
    for i in range(len(raw_grades)):
        start = max(0, i - SMOOTHING_WINDOW // 2)
        end = min(len(raw_grades), i + SMOOTHING_WINDOW // 2 + 1)
        window = raw_grades[start:end]
        smoothed.append(sum(window) / len(window))

    return smoothed


def compute_gap(activity: Activity, session: Session) -> GAPResult:
    """Compute Grade-Adjusted Pace for an activity.

    Queries altitude and distance streams, computes grade per segment,
    applies Minetti cost model, and returns distance-weighted average GAP.

    Args:
        activity: The activity to compute GAP for.
        session: Database session.

    Returns:
        GAPResult with overall GAP, per-lap GAPs, and availability flag.
    """
    unavailable = GAPResult(
        overall_gap=None, lap_gaps=[], grade_profile=[], available=False
    )

    # Get required streams
    streams = get_activity_streams(
        session, activity.id, stream_types=["altitude", "distance"]
    )
    stream_map: dict[str, list] = {}
    for s in streams:
        try:
            stream_map[s.stream_type] = json.loads(s.data)
        except (json.JSONDecodeError, TypeError):
            continue

    altitude = stream_map.get("altitude")
    distance = stream_map.get("distance")

    if not altitude or not distance:
        return unavailable

    if len(altitude) < MIN_STREAM_POINTS or len(distance) < MIN_STREAM_POINTS:
        return unavailable

    # Compute grades
    grades = compute_grades(altitude, distance)
    if not grades:
        return unavailable

    # Compute distance-weighted cost ratio
    n = min(len(grades), len(distance) - 1)
    total_cost_distance = 0.0
    total_distance = 0.0

    for i in range(n):
        seg_dist = distance[i + 1] - distance[i]
        if seg_dist <= 0:
            continue
        cost_ratio = minetti_cost(grades[i]) / FLAT_COST
        total_cost_distance += cost_ratio * seg_dist
        total_distance += seg_dist

    if total_distance <= 0 or not activity.average_speed or activity.average_speed <= 0:
        return unavailable

    avg_cost_ratio = total_cost_distance / total_distance
    # GAP = actual_pace adjusted by cost ratio
    # If avg_cost_ratio > 1 (harder than flat), GAP should be faster (higher m/s)
    overall_gap = activity.average_speed * avg_cost_ratio

    # Compute per-lap GAP
    laps = get_laps(session, activity.id)
    lap_gaps: list[float | None] = []

    for lap in laps:
        lap_gap = _compute_lap_gap(lap, grades, distance)
        lap_gaps.append(lap_gap)

    return GAPResult(
        overall_gap=overall_gap,
        lap_gaps=lap_gaps,
        grade_profile=grades,
        available=True,
    )


def _compute_lap_gap(
    lap: Lap, grades: list[float], distance_stream: list[float]
) -> float | None:
    """Compute GAP for a single lap using its stream index range."""
    if lap.start_index >= lap.end_index:
        return None

    start = lap.start_index
    end = min(lap.end_index, len(grades), len(distance_stream) - 1)

    if start >= end or start >= len(grades):
        return None

    total_cost_distance = 0.0
    total_distance = 0.0

    for i in range(start, end):
        if i >= len(grades) or i + 1 >= len(distance_stream):
            break
        seg_dist = distance_stream[i + 1] - distance_stream[i]
        if seg_dist <= 0:
            continue
        cost_ratio = minetti_cost(grades[i]) / FLAT_COST
        total_cost_distance += cost_ratio * seg_dist
        total_distance += seg_dist

    if total_distance <= 0 or not lap.average_speed or lap.average_speed <= 0:
        return None

    avg_cost_ratio = total_cost_distance / total_distance
    return lap.average_speed * avg_cost_ratio


def compute_effort_score(
    activity: Activity,
    gap_result: GAPResult,
    stats: dict,
) -> EffortScoreResult:
    """Compute a 0-100 effort score for an activity.

    Components (each 0-25, or 0-33.3 if no HR):
    - Duration: Percentile against user's activity history
    - GAP: Percentile of GAP speed (faster = higher)
    - Heart Rate: Avg HR as % of estimated max HR (220 - age, default 190)
    - Elevation: Elevation gain per km, percentiled against history

    Args:
        activity: The activity.
        gap_result: Computed GAP for this activity.
        stats: User activity stats from get_user_activity_stats().

    Returns:
        EffortScoreResult with score and component breakdowns.
    """
    has_hr = activity.average_heartrate is not None and activity.average_heartrate > 0

    # Duration component
    duration_pct = _percentile(activity.moving_time or 0, stats.get("durations", []))

    # GAP component (faster GAP = higher effort)
    gap_speed = gap_result.overall_gap if gap_result.available else activity.average_speed
    gap_pct = _percentile(gap_speed or 0, stats.get("gap_speeds", []))

    # Elevation component (gain per km)
    dist_km = (activity.distance or 0) / 1000.0
    elev_per_km = (activity.total_elevation_gain or 0) / dist_km if dist_km > 0 else 0
    elev_pct = _percentile(elev_per_km, stats.get("elev_per_kms", []))

    if has_hr:
        # HR component: avg HR as % of estimated max (default max HR = 190)
        max_hr = stats.get("estimated_max_hr", 190)
        hr_ratio = (activity.average_heartrate or 0) / max_hr
        hr_component = min(hr_ratio * 25.0, 25.0)

        duration_component = duration_pct * 25.0
        gap_component = gap_pct * 25.0
        elevation_component = elev_pct * 25.0
    else:
        hr_component = None
        duration_component = duration_pct * 33.33
        gap_component = gap_pct * 33.33
        elevation_component = elev_pct * 33.33

    total = duration_component + gap_component + elevation_component
    if hr_component is not None:
        total += hr_component

    score = max(0, min(100, round(total)))

    return EffortScoreResult(
        score=score,
        duration_component=duration_component,
        gap_component=gap_component,
        hr_component=hr_component,
        elevation_component=elevation_component,
    )


def _percentile(value: float, distribution: list[float]) -> float:
    """Compute percentile of value within distribution (0.0 to 1.0)."""
    if not distribution:
        return 0.5
    count_below = sum(1 for v in distribution if v < value)
    return count_below / len(distribution)


def get_user_activity_stats(
    session: Session, activity_type: str = "Run"
) -> dict:
    """Build percentile distributions from user's activity history.

    Queries all activities of given type to build distributions for
    duration, GAP speed, and elevation gain per km.

    Returns:
        Dict with 'durations', 'gap_speeds', 'elev_per_kms', 'estimated_max_hr'.
    """
    activities = get_activities(
        session,
        activity_type=activity_type,
        sort="date",
        limit=10000,
        offset=0,
    )

    durations: list[float] = []
    gap_speeds: list[float] = []
    elev_per_kms: list[float] = []
    max_hr_seen = 0.0

    for a in activities:
        if not a.distance or a.distance <= 0 or not a.moving_time or a.moving_time <= 0:
            continue

        durations.append(float(a.moving_time))

        # Use actual speed as proxy for GAP in stats (computing full GAP
        # for all activities here would be too expensive)
        if a.average_speed and a.average_speed > 0:
            gap_speeds.append(a.average_speed)

        dist_km = a.distance / 1000.0
        if dist_km > 0 and a.total_elevation_gain is not None:
            elev_per_kms.append(a.total_elevation_gain / dist_km)

        if a.max_heartrate and a.max_heartrate > max_hr_seen:
            max_hr_seen = a.max_heartrate

    # Estimated max HR: use observed max if available, else default 190
    estimated_max_hr = max_hr_seen if max_hr_seen > 0 else 190.0

    return {
        "durations": durations,
        "gap_speeds": gap_speeds,
        "elev_per_kms": elev_per_kms,
        "estimated_max_hr": estimated_max_hr,
    }


def get_effort_trend(
    session: Session,
    *,
    time_window: str = "90d",
    activity_type: str = "Run",
) -> dict:
    """Compute effort trend across activities over a time window.

    Returns dict with trend summary and per-activity data including
    GAP and effort scores.
    """
    after = _parse_time_window(time_window)

    activities = get_activities(
        session,
        activity_type=activity_type,
        after=after,
        sort="date",
        limit=10000,
        offset=0,
    )

    # Filter to valid activities
    valid = [
        a for a in activities
        if a.distance and a.distance > 0
        and a.moving_time and a.moving_time > 0
        and a.start_date
    ]

    if not valid:
        return {
            "time_window": time_window,
            "activity_type": activity_type,
            "trend": "stable",
            "avg_gap": None,
            "avg_gap_formatted": None,
            "avg_effort_score": 0,
            "activity_count": 0,
            "activities": [],
        }

    # Get stats for effort scoring
    stats = get_user_activity_stats(session, activity_type)

    entries = []
    gap_values: list[float] = []
    gap_dates: list[datetime] = []
    effort_scores: list[int] = []

    for a in valid:
        gap_result = compute_gap(a, session)

        effort = compute_effort_score(a, gap_result, stats)

        gap_val = gap_result.overall_gap
        if gap_val and gap_result.available:
            gap_values.append(gap_val)
            gap_dates.append(a.start_date)

        entries.append({
            "activity_id": a.id,
            "activity_name": a.name,
            "date": a.start_date.isoformat() if a.start_date else None,
            "distance": a.distance,
            "actual_pace": a.average_speed,
            "gap": gap_val,
            "gap_available": gap_result.available,
            "effort_score": effort.score,
            "elevation_gain": a.total_elevation_gain or 0,
            "average_heartrate": a.average_heartrate,
        })
        effort_scores.append(effort.score)

    # Reverse to chronological order (query returns descending)
    entries.reverse()
    gap_values.reverse()
    gap_dates.reverse()

    # Trend direction
    trend = _compute_trend_direction(gap_values, gap_dates)

    # Averages
    avg_gap = sum(gap_values) / len(gap_values) if gap_values else None
    avg_effort = sum(effort_scores) / len(effort_scores) if effort_scores else 0

    return {
        "time_window": time_window,
        "activity_type": activity_type,
        "trend": trend,
        "avg_gap": avg_gap,
        "avg_gap_formatted": None,  # Formatted by caller with units
        "avg_effort_score": round(avg_effort),
        "activity_count": len(entries),
        "activities": entries,
    }


def _compute_trend_direction(
    gap_values: list[float], dates: list[datetime]
) -> str:
    """Compute trend direction using simple linear regression on GAP values.

    Classifies as:
    - "improving": GAP getting faster (positive slope in m/s) > threshold
    - "declining": GAP getting slower (negative slope in m/s) > threshold
    - "stable": Within threshold

    Threshold: ~2 sec/km/month change.
    """
    if len(gap_values) < 3:
        return "stable"

    # Convert dates to days since first date
    base = dates[0]
    x = [(d - base).total_seconds() / 86400.0 for d in dates]
    y = gap_values

    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y, strict=True))
    sum_x2 = sum(xi * xi for xi in x)

    denom = n * sum_x2 - sum_x * sum_x
    if denom == 0:
        return "stable"

    slope = (n * sum_xy - sum_x * sum_y) / denom

    # slope is m/s per day. Convert to sec/km per month.
    # m/s change per day → sec/km change per day = -1000/v^2 * slope_per_day
    # Approximate: 2 sec/km/month ≈ 0.067 sec/km/day
    # At ~4 m/s pace: 1000/(4^2) = 62.5 sec/km per m/s
    # So 0.067 sec/km/day ≈ 0.067/62.5 = 0.00107 m/s/day
    # Monthly threshold: 0.032 m/s/month ≈ 0.001 m/s/day
    threshold = 0.001  # m/s per day

    if slope > threshold:
        return "improving"  # GAP speed increasing = getting faster
    elif slope < -threshold:
        return "declining"  # GAP speed decreasing = getting slower
    return "stable"


def _parse_time_window(last: str) -> datetime | None:
    """Parse a time window string like '90d', '6m', '1y' into a datetime cutoff."""
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
