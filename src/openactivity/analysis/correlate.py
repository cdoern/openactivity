"""Cross-activity correlation engine.

Computes Pearson and Spearman correlations between weekly training metrics
with optional lag analysis for delayed-effect discovery.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from scipy.stats import pearsonr, spearmanr

from openactivity.analysis.blocks import aggregate_weeks
from openactivity.db.queries import get_activities

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Minimum weeks for meaningful correlation
MIN_SAMPLES = 4
LOW_CONFIDENCE_THRESHOLD = 12

# Strength thresholds (Cohen's conventions)
WEAK_THRESHOLD = 0.3
STRONG_THRESHOLD = 0.7

# Valid lag values
VALID_LAGS = [0, 1, 2, 4]

# Supported metrics registry
SUPPORTED_METRICS: dict[str, str] = {
    "weekly_distance": "Total distance (meters)",
    "weekly_duration": "Total moving time (seconds)",
    "weekly_elevation": "Total elevation gain (meters)",
    "avg_pace": "Distance-weighted average pace (s/km)",
    "avg_hr": "Average heart rate",
    "max_hr": "Maximum heart rate",
    "activity_count": "Number of activities",
    "rest_days": "Days without activity (0-7)",
    "longest_run": "Longest single activity distance (meters)",
}


# ---- Metric computation functions ----


def _weekly_distance(week: dict) -> float | None:
    return week.get("total_distance", 0.0)


def _weekly_duration(week: dict) -> float | None:
    return float(week.get("total_duration", 0))


def _weekly_elevation(week: dict) -> float | None:
    activities = week.get("activities", [])
    if not activities:
        return 0.0
    return sum(a.total_elevation_gain or 0 for a in activities)


def _avg_pace(week: dict) -> float | None:
    activities = week.get("activities", [])
    if not activities:
        return None
    total_dist = 0.0
    total_time = 0.0
    for a in activities:
        d = a.distance or 0
        t = a.moving_time or 0
        if d > 0 and t > 0:
            total_dist += d
            total_time += t
    if total_dist <= 0:
        return None
    # Pace in seconds per km
    return total_time / (total_dist / 1000)


def _avg_hr(week: dict) -> float | None:
    activities = week.get("activities", [])
    hr_values = []
    for a in activities:
        if a.average_heartrate and a.average_heartrate > 0:
            hr_values.append(a.average_heartrate)
    if not hr_values:
        return None
    return sum(hr_values) / len(hr_values)


def _max_hr(week: dict) -> float | None:
    activities = week.get("activities", [])
    max_vals = []
    for a in activities:
        if a.max_heartrate and a.max_heartrate > 0:
            max_vals.append(a.max_heartrate)
    if not max_vals:
        return None
    return float(max(max_vals))


def _activity_count(week: dict) -> float | None:
    return float(week.get("activity_count", 0))


def _rest_days(week: dict) -> float | None:
    activities = week.get("activities", [])
    if not activities:
        return 7.0
    active_days = set()
    for a in activities:
        if a.start_date:
            active_days.add(a.start_date.date())
    return float(7 - len(active_days))


def _longest_run(week: dict) -> float | None:
    activities = week.get("activities", [])
    if not activities:
        return 0.0
    distances = [a.distance for a in activities if a.distance and a.distance > 0]
    return float(max(distances)) if distances else 0.0


# Registry mapping metric names to functions
METRIC_FUNCTIONS: dict[str, callable] = {
    "weekly_distance": _weekly_distance,
    "weekly_duration": _weekly_duration,
    "weekly_elevation": _weekly_elevation,
    "avg_pace": _avg_pace,
    "avg_hr": _avg_hr,
    "max_hr": _max_hr,
    "activity_count": _activity_count,
    "rest_days": _rest_days,
    "longest_run": _longest_run,
}


def compute_weekly_metrics(
    session: Session,
    activity_type: str = "Run",
    time_window: str = "1y",
    provider: str | None = None,
) -> list[dict]:
    """Compute all weekly metrics from activity data.

    Returns list of WeeklyMetrics dicts, one per ISO week.
    """
    after = _parse_time_window(time_window)
    activities = get_activities(
        session, activity_type=activity_type, after=after,
        provider=provider, sort="date", limit=10000, offset=0,
    )
    valid = [
        a for a in activities
        if a.distance and a.distance > 0
        and a.moving_time and a.moving_time > 0
        and a.start_date
    ]

    weeks = aggregate_weeks(valid, after=after)

    # Extend each week with all metric values
    for week in weeks:
        for name, func in METRIC_FUNCTIONS.items():
            week[f"metric_{name}"] = func(week)

    return weeks


def compute_correlation(
    x_values: list[float],
    y_values: list[float],
) -> dict:
    """Compute Pearson and Spearman correlations.

    Args:
        x_values: X metric values.
        y_values: Y metric values (same length).

    Returns:
        Dict with pearson_r, pearson_p, spearman_r, spearman_p, or error.
    """
    if len(x_values) != len(y_values):
        return {"error": "length_mismatch", "message": "X and Y must have same length."}

    if len(x_values) < MIN_SAMPLES:
        return {
            "error": "insufficient_data",
            "message": f"Need at least {MIN_SAMPLES} data points. Found {len(x_values)}.",
        }

    # Check for zero variance
    if len(set(x_values)) <= 1:
        return {
            "error": "zero_variance",
            "message": "X metric has no variance (all values identical).",
        }
    if len(set(y_values)) <= 1:
        return {
            "error": "zero_variance",
            "message": "Y metric has no variance (all values identical).",
        }

    p_r, p_p = pearsonr(x_values, y_values)
    s_r, s_p = spearmanr(x_values, y_values)

    return {
        "pearson_r": round(float(p_r), 4),
        "pearson_p": round(float(p_p), 4),
        "spearman_r": round(float(s_r), 4),
        "spearman_p": round(float(s_p), 4),
    }


def classify_strength(r: float) -> str:
    """Classify correlation strength."""
    abs_r = abs(r)
    if abs_r >= STRONG_THRESHOLD:
        return "strong"
    if abs_r >= WEAK_THRESHOLD:
        return "moderate"
    return "weak"


def interpret_direction(x_metric: str, y_metric: str, r: float) -> str:
    """Generate human-readable direction interpretation."""
    x_display = x_metric.replace("_", " ")
    y_display = y_metric.replace("_", " ")

    if abs(r) < 0.1:
        return f"No meaningful association between {x_display} and {y_display}"

    association = "higher" if r > 0 else "lower"

    # Special handling for pace (lower is faster)
    if y_metric == "avg_pace":
        association = "slower" if r > 0 else "faster"

    return f"More {x_display} is associated with {association} {y_display}"


def correlate(
    session: Session,
    *,
    x_metric: str,
    y_metric: str,
    time_window: str = "1y",
    activity_type: str = "Run",
    lag: int = 0,
    provider: str | None = None,
) -> dict:
    """Orchestrate correlation computation.

    Args:
        session: Database session.
        x_metric: X-axis metric name.
        y_metric: Y-axis metric name.
        time_window: Time window string (6m, 1y, all).
        activity_type: Activity type filter.
        lag: Lag offset in weeks.

    Returns:
        CorrelationResult dict.
    """
    # Validate metric names
    if x_metric not in SUPPORTED_METRICS:
        return {
            "error": "invalid_metric",
            "message": (
                f"Unknown metric: '{x_metric}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_METRICS.keys()))}"
            ),
        }
    if y_metric not in SUPPORTED_METRICS:
        return {
            "error": "invalid_metric",
            "message": (
                f"Unknown metric: '{y_metric}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_METRICS.keys()))}"
            ),
        }

    # Validate lag
    if lag not in VALID_LAGS:
        return {
            "error": "invalid_lag",
            "message": f"Invalid lag: {lag}. Supported values: {VALID_LAGS}",
        }

    # Compute weekly metrics
    weeks = compute_weekly_metrics(session, activity_type, time_window, provider=provider)
    total_weeks = len(weeks)

    if total_weeks < MIN_SAMPLES:
        return {
            "error": "insufficient_data",
            "message": (
                f"Need at least {MIN_SAMPLES} weeks of data. Found {total_weeks}."
            ),
            "total_weeks": total_weeks,
        }

    # Extract metric values
    x_key = f"metric_{x_metric}"
    y_key = f"metric_{y_metric}"

    # Apply lag: pair X[i] with Y[i+lag]
    paired = []
    for i in range(len(weeks) - lag):
        x_val = weeks[i].get(x_key)
        y_val = weeks[i + lag].get(y_key)
        if x_val is not None and y_val is not None:
            paired.append({
                "x": x_val,
                "y": y_val,
                "week_key": weeks[i]["week_key"],
                "y_week_key": weeks[i + lag]["week_key"],
            })

    if len(paired) < MIN_SAMPLES:
        return {
            "error": "insufficient_data",
            "message": (
                f"Need at least {MIN_SAMPLES} weeks with both metrics present. "
                f"Found {len(paired)} usable weeks (of {total_weeks} total)."
            ),
            "sample_size": len(paired),
            "total_weeks": total_weeks,
        }

    x_values = [p["x"] for p in paired]
    y_values = [p["y"] for p in paired]

    # Compute correlation
    result = compute_correlation(x_values, y_values)
    if "error" in result:
        result["total_weeks"] = total_weeks
        result["sample_size"] = len(paired)
        return result

    # Classify and interpret
    strength = classify_strength(result["pearson_r"])
    direction = interpret_direction(x_metric, y_metric, result["pearson_r"])
    significant = result["pearson_p"] < 0.05
    low_confidence = len(paired) < LOW_CONFIDENCE_THRESHOLD

    return {
        "x_metric": x_metric,
        "y_metric": y_metric,
        "lag": lag,
        "time_window": time_window,
        "activity_type": activity_type,
        "pearson_r": result["pearson_r"],
        "pearson_p": result["pearson_p"],
        "spearman_r": result["spearman_r"],
        "spearman_p": result["spearman_p"],
        "strength": strength,
        "direction": direction,
        "significant": significant,
        "low_confidence": low_confidence,
        "sample_size": len(paired),
        "total_weeks": total_weeks,
        "data_points": paired,
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
