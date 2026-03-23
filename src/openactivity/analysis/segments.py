"""Segment trend analysis.

Computes linear regression on segment effort times over time to detect
performance trends (improving, declining, stable). Optionally adjusts
for heart rate to distinguish fitness gains from effort differences.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from scipy.stats import linregress

from openactivity.db.queries import (
    get_segment_by_id,
    get_segment_efforts_chronological,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Minimum efforts for trend analysis
MIN_EFFORTS = 3

# Stable threshold: ±1 second per month
STABLE_THRESHOLD = 1.0

# Days per month for conversion
DAYS_PER_MONTH = 30.44


def _classify_trend(rate_per_month: float) -> str:
    """Classify trend direction based on rate of change.

    Negative rate = improving (getting faster).
    Positive rate = declining (getting slower).
    Within ±1 sec/month = stable.
    """
    if rate_per_month < -STABLE_THRESHOLD:
        return "improving"
    if rate_per_month > STABLE_THRESHOLD:
        return "declining"
    return "stable"


def _build_effort_summary(effort, best_time: int) -> dict:
    """Build an EffortSummary dict from a SegmentEffort."""
    hr = effort.average_heartrate
    hr_normalized = None
    if hr and hr > 0 and effort.elapsed_time and effort.elapsed_time > 0:
        hr_normalized = round(effort.elapsed_time / hr, 4)

    return {
        "date": effort.start_date,
        "elapsed_time": effort.elapsed_time,
        "average_heartrate": hr,
        "delta_from_best": effort.elapsed_time - best_time,
        "hr_normalized_time": hr_normalized,
    }


def _compute_trend(x_days: list[float], y_times: list[float]) -> dict:
    """Run linear regression and return trend result."""
    result = linregress(x_days, y_times)
    rate_per_month = result.slope * DAYS_PER_MONTH

    return {
        "direction": _classify_trend(rate_per_month),
        "rate_of_change": round(rate_per_month, 2),
        "rate_unit": "seconds/month",
        "r_squared": round(result.rvalue ** 2, 4),
    }


def _compute_hr_adjusted_trend(efforts: list) -> dict | None:
    """Compute HR-adjusted trend using time/HR normalization.

    Only uses efforts that have HR data. Returns None if fewer than
    MIN_EFFORTS efforts have HR data.
    """
    hr_efforts = [
        e for e in efforts
        if e.average_heartrate and e.average_heartrate > 0
        and e.elapsed_time and e.elapsed_time > 0
        and e.start_date
    ]

    if len(hr_efforts) < MIN_EFFORTS:
        return None

    first_date = hr_efforts[0].start_date
    x_days = [(e.start_date - first_date).total_seconds() / 86400 for e in hr_efforts]
    y_normalized = [e.elapsed_time / e.average_heartrate for e in hr_efforts]

    result = linregress(x_days, y_normalized)
    rate_per_month = result.slope * DAYS_PER_MONTH

    return {
        "direction": _classify_trend(rate_per_month),
        "rate_of_change": round(rate_per_month, 4),
        "rate_unit": "normalized_units/month",
        "r_squared": round(result.rvalue ** 2, 4),
        "effort_count": len(hr_efforts),
    }


def compute_segment_trend(session: Session, segment_id: int) -> dict:
    """Compute trend analysis for a segment.

    Returns a SegmentTrend dict with direction, rate of change,
    effort history, and optional HR-adjusted trend.
    """
    segment = get_segment_by_id(session, segment_id)
    if not segment:
        return {
            "error": "segment_not_found",
            "message": (
                f"Segment {segment_id} not found. "
                "Run 'openactivity strava sync' to fetch segment data."
            ),
        }

    efforts = get_segment_efforts_chronological(session, segment_id)

    # Filter to efforts with valid date and time
    valid_efforts = [
        e for e in efforts
        if e.start_date and e.elapsed_time and e.elapsed_time > 0
    ]

    if not valid_efforts:
        return {
            "error": "no_efforts",
            "message": (
                f"No efforts found for segment {segment_id}. "
                "Run 'openactivity strava sync' to fetch effort data."
            ),
        }

    # Build effort summaries
    best_time = min(e.elapsed_time for e in valid_efforts)
    effort_summaries = [_build_effort_summary(e, best_time) for e in valid_efforts]

    # Find best, worst, recent
    best_effort = min(effort_summaries, key=lambda e: e["elapsed_time"])
    worst_effort = max(effort_summaries, key=lambda e: e["elapsed_time"])
    recent_effort = effort_summaries[-1]

    result = {
        "segment_id": segment.id,
        "segment_name": segment.name,
        "distance": segment.distance,
        "effort_count": len(valid_efforts),
        "date_range_start": valid_efforts[0].start_date,
        "date_range_end": valid_efforts[-1].start_date,
        "best_effort": best_effort,
        "worst_effort": worst_effort,
        "recent_effort": recent_effort,
        "efforts": effort_summaries,
    }

    # Need at least MIN_EFFORTS for trend analysis
    if len(valid_efforts) < MIN_EFFORTS:
        result["error"] = "insufficient_efforts"
        result["message"] = (
            f"Need at least {MIN_EFFORTS} efforts for trend analysis. "
            f"You have {len(valid_efforts)}."
        )
        return result

    # Compute raw trend via linear regression
    first_date = valid_efforts[0].start_date
    x_days = [(e.start_date - first_date).total_seconds() / 86400 for e in valid_efforts]
    y_times = [float(e.elapsed_time) for e in valid_efforts]

    result["trend"] = _compute_trend(x_days, y_times)

    # Compute HR-adjusted trend if possible
    hr_trend = _compute_hr_adjusted_trend(valid_efforts)
    if hr_trend:
        result["hr_adjusted"] = hr_trend

    return result


def compute_segment_trend_indicator(session: Session, segment_id: int) -> tuple[str, str]:
    """Compute a compact trend indicator for the segments list.

    Returns (indicator, rate_str) tuple:
    - indicator: "↑", "↓", "→", or "—"
    - rate_str: e.g., "-3.2/mo" or "—"
    """
    efforts = get_segment_efforts_chronological(session, segment_id)
    valid = [
        e for e in efforts
        if e.start_date and e.elapsed_time and e.elapsed_time > 0
    ]

    if len(valid) < MIN_EFFORTS:
        return ("—", "—")

    first_date = valid[0].start_date
    x_days = [(e.start_date - first_date).total_seconds() / 86400 for e in valid]
    y_times = [float(e.elapsed_time) for e in valid]

    result = linregress(x_days, y_times)
    rate_per_month = result.slope * DAYS_PER_MONTH

    direction = _classify_trend(rate_per_month)
    if direction == "improving":
        indicator = "↑"
    elif direction == "declining":
        indicator = "↓"
    else:
        indicator = "→"

    rate_str = f"{rate_per_month:+.1f}/mo"
    return (indicator, rate_str)
