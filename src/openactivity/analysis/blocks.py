"""Training block / periodization detection.

Classifies weeks into training phases (base, build, peak, recovery) based on
volume and intensity patterns. Groups consecutive similar weeks into named
training blocks.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from openactivity.db.queries import get_activities

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Phase classifications
RECOVERY = "recovery"
BASE = "base"
BUILD = "build"
PEAK = "peak"

# Volume threshold: recovery is < this fraction of 4-week rolling avg
VOLUME_RECOVERY_THRESHOLD = 0.70

# Intensity thresholds (0-100 scale)
INTENSITY_BASE_CEILING = 60  # Below this = low intensity (base)
INTENSITY_PEAK_FLOOR = 70  # Above this = high intensity (peak candidate)

# Minimum weeks for meaningful block detection
MIN_WEEKS = 4

# Gap threshold: >14 days with no activities forces a block boundary
GAP_THRESHOLD_DAYS = 14

# Rolling average window
ROLLING_WINDOW = 4

# Phase descriptions for user context
PHASE_DESCRIPTIONS = {
    RECOVERY: "Low volume — rest and adaptation",
    BASE: "High volume, low intensity — building aerobic fitness",
    BUILD: "Rising volume and intensity — preparing for performance",
    PEAK: "High intensity, tapering volume — race-ready sharpening",
}


def aggregate_weeks(
    activities: list, after: datetime | None = None
) -> list[dict]:
    """Group activities into ISO weeks and compute per-week metrics.

    Args:
        activities: List of Activity objects sorted by date.
        after: Optional cutoff date for filtering.

    Returns:
        List of WeekSummary dicts sorted chronologically.
    """
    if not activities:
        return []

    # Group activities by ISO week
    week_map: dict[str, dict] = {}

    for a in activities:
        if not a.start_date:
            continue
        if after and a.start_date < after:
            continue

        # ISO week: Monday-based
        iso_year, iso_week, _ = a.start_date.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"

        if week_key not in week_map:
            # Compute Monday of this ISO week
            monday = a.start_date - timedelta(days=a.start_date.weekday())
            monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
            week_map[week_key] = {
                "week_key": week_key,
                "week_start": monday,
                "week_end": monday + timedelta(days=6),
                "total_distance": 0.0,
                "total_duration": 0,
                "activity_count": 0,
                "activities": [],
            }

        week = week_map[week_key]
        week["total_distance"] += a.distance or 0
        week["total_duration"] += a.moving_time or 0
        week["activity_count"] += 1
        week["activities"].append(a)

    # Sort chronologically
    weeks = sorted(week_map.values(), key=lambda w: w["week_start"])

    # Fill in empty weeks between first and last
    if len(weeks) >= 2:
        weeks = _fill_empty_weeks(weeks)

    return weeks


def _fill_empty_weeks(weeks: list[dict]) -> list[dict]:
    """Fill gaps between weeks with zero-volume weeks."""
    filled: list[dict] = []
    for i, week in enumerate(weeks):
        filled.append(week)
        if i < len(weeks) - 1:
            next_week = weeks[i + 1]
            current_end = week["week_end"]
            next_start = next_week["week_start"]
            gap = (next_start - current_end).days
            # Fill missing weeks (gap > 7 days means missing weeks)
            if gap > 7:
                cursor = current_end + timedelta(days=1)
                while cursor < next_start:
                    monday = cursor - timedelta(days=cursor.weekday())
                    monday = monday.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    iso_year, iso_week, _ = monday.isocalendar()
                    filled.append({
                        "week_key": f"{iso_year}-W{iso_week:02d}",
                        "week_start": monday,
                        "week_end": monday + timedelta(days=6),
                        "total_distance": 0.0,
                        "total_duration": 0,
                        "activity_count": 0,
                        "activities": [],
                    })
                    cursor += timedelta(days=7)
    return filled


def compute_week_intensity(
    week: dict,
    estimated_max_hr: float = 190.0,
    pace_distribution: list[float] | None = None,
) -> tuple[float, str]:
    """Compute normalized intensity (0-100) for a week.

    Uses avg HR as % of max HR when available, falls back to pace percentile.

    Args:
        week: WeekSummary dict with 'activities' list.
        estimated_max_hr: User's estimated max HR.
        pace_distribution: List of pace values (m/s) for percentile ranking.

    Returns:
        Tuple of (intensity_score, source).
    """
    activities = week.get("activities", [])
    if not activities:
        return 0.0, "default"

    # Try HR-based intensity
    hr_values = []
    for a in activities:
        if a.average_heartrate and a.average_heartrate > 0:
            hr_values.append(a.average_heartrate)

    if hr_values:
        avg_hr = sum(hr_values) / len(hr_values)
        intensity = min(100.0, (avg_hr / estimated_max_hr) * 100.0)
        return intensity, "hr"

    # Fall back to pace-based intensity
    pace_values = []
    for a in activities:
        if a.average_speed and a.average_speed > 0:
            pace_values.append(a.average_speed)

    if pace_values and pace_distribution:
        avg_pace = sum(pace_values) / len(pace_values)
        # Higher speed = higher intensity
        count_below = sum(1 for p in pace_distribution if p < avg_pace)
        intensity = (count_below / len(pace_distribution)) * 100.0
        return intensity, "pace"

    return 50.0, "default"


def classify_weeks(weeks: list[dict]) -> list[dict]:
    """Classify each week into a training phase.

    Uses 4-week rolling average volume as baseline.
    Rules:
    - Recovery: volume < 70% of rolling avg
    - Base: volume >= 70% AND intensity < 60
    - Build: volume >= 70% AND intensity >= 60 AND volume rising
    - Peak: intensity >= 70 AND volume tapering (2+ weeks)

    Args:
        weeks: List of WeekSummary dicts with intensity already computed.

    Returns:
        Same list with 'classification' added to each week.
    """
    for i, week in enumerate(weeks):
        volume = week["total_distance"]
        intensity = week.get("avg_intensity", 50.0)

        # Compute rolling average volume (4-week window)
        if i >= ROLLING_WINDOW:
            window = weeks[i - ROLLING_WINDOW : i]
            rolling_avg = sum(w["total_distance"] for w in window) / ROLLING_WINDOW
        elif i > 0:
            window = weeks[:i]
            rolling_avg = sum(w["total_distance"] for w in window) / len(window)
        else:
            rolling_avg = volume if volume > 0 else 1.0

        # Avoid division by zero
        if rolling_avg <= 0:
            rolling_avg = 1.0

        volume_ratio = volume / rolling_avg

        # Check for tapering (volume decreasing for 2+ consecutive weeks)
        is_tapering = False
        if i >= 2:
            is_tapering = (
                weeks[i - 1]["total_distance"] < weeks[i - 2]["total_distance"]
                and volume < weeks[i - 1]["total_distance"]
            )

        # Classification rules
        if volume_ratio < VOLUME_RECOVERY_THRESHOLD:
            classification = RECOVERY
        elif intensity >= INTENSITY_PEAK_FLOOR and is_tapering:
            classification = PEAK
        elif intensity >= INTENSITY_BASE_CEILING and volume_ratio >= 1.0:
            classification = BUILD
        else:
            classification = BASE

        week["classification"] = classification
        week["volume_ratio"] = volume_ratio

    return weeks


def group_into_blocks(weeks: list[dict]) -> list[dict]:
    """Group consecutive weeks with same classification into blocks.

    Forces block boundary on gaps >14 days with no activities.

    Args:
        weeks: Classified WeekSummary dicts.

    Returns:
        List of TrainingBlock dicts.
    """
    if not weeks:
        return []

    blocks: list[dict] = []
    current_block: dict | None = None

    for i, week in enumerate(weeks):
        classification = week.get("classification", BASE)

        # Check for gap forcing block boundary
        has_gap = False
        if i > 0:
            prev_end = weeks[i - 1]["week_end"]
            curr_start = week["week_start"]
            gap_days = (curr_start - prev_end).days
            has_gap = gap_days > GAP_THRESHOLD_DAYS

        # Start new block if classification changed or gap detected
        if current_block is None or classification != current_block["phase"] or has_gap:
            if current_block is not None:
                _finalize_block(current_block)
                blocks.append(current_block)

            current_block = {
                "phase": classification,
                "start_date": week["week_start"],
                "end_date": week["week_end"],
                "week_count": 0,
                "total_distance": 0.0,
                "activity_count": 0,
                "intensity_sum": 0.0,
                "is_current": False,
            }

        # Add week to current block
        current_block["end_date"] = week["week_end"]
        current_block["week_count"] += 1
        current_block["total_distance"] += week["total_distance"]
        current_block["activity_count"] += week["activity_count"]
        current_block["intensity_sum"] += week.get("avg_intensity", 50.0)

    # Finalize last block
    if current_block is not None:
        current_block["is_current"] = True
        _finalize_block(current_block)
        blocks.append(current_block)

    return blocks


def _finalize_block(block: dict) -> None:
    """Compute derived metrics for a block."""
    wc = block["week_count"]
    block["avg_weekly_distance"] = block["total_distance"] / wc if wc > 0 else 0
    block["avg_intensity"] = round(block["intensity_sum"] / wc) if wc > 0 else 0
    # Clean up internal field
    del block["intensity_sum"]


def detect_blocks(
    session: Session,
    *,
    time_window: str = "6m",
    activity_type: str = "Run",
) -> dict:
    """Detect training blocks from activity data.

    Orchestrates: query activities, aggregate weeks, compute intensity,
    classify weeks, group blocks.

    Returns:
        BlocksResult dict with blocks, weeks, current phase, and metadata.
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

    # Filter valid activities
    valid = [
        a for a in activities
        if a.distance and a.distance > 0
        and a.moving_time and a.moving_time > 0
        and a.start_date
    ]

    # Aggregate into weeks
    weeks = aggregate_weeks(valid, after=after)

    if len(weeks) < MIN_WEEKS:
        return {
            "error": "insufficient_data",
            "message": (
                f"At least {MIN_WEEKS} weeks of activity data are needed "
                f"for block detection. Found {len(weeks)} weeks."
            ),
            "weeks_found": len(weeks),
            "time_window": time_window,
            "activity_type": activity_type,
        }

    # Build pace distribution for intensity fallback
    pace_distribution = [
        a.average_speed for a in valid
        if a.average_speed and a.average_speed > 0
    ]

    # Compute estimated max HR
    max_hr_seen = max(
        (a.max_heartrate for a in valid if a.max_heartrate and a.max_heartrate > 0),
        default=0,
    )
    estimated_max_hr = max_hr_seen if max_hr_seen > 0 else 190.0

    # Compute intensity per week
    for week in weeks:
        intensity, source = compute_week_intensity(
            week, estimated_max_hr, pace_distribution
        )
        week["avg_intensity"] = intensity
        week["intensity_source"] = source

    # Classify weeks
    classify_weeks(weeks)

    # Group into blocks
    blocks = group_into_blocks(weeks)

    current_phase = blocks[-1]["phase"] if blocks else BASE

    return {
        "time_window": time_window,
        "activity_type": activity_type,
        "current_phase": current_phase,
        "current_phase_description": PHASE_DESCRIPTIONS.get(current_phase, ""),
        "total_weeks": len(weeks),
        "total_activities": sum(w["activity_count"] for w in weeks),
        "blocks": blocks,
    }


def _parse_time_window(last: str) -> datetime | None:
    """Parse a time window string into a datetime cutoff."""
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
