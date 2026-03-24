"""Fitness / Fatigue / Form model (ATL / CTL / TSB).

Implements the classic Banister impulse-response model using TRIMP-based
Training Stress Scores computed from heart rate data.  Works with activity
data from both Strava and Garmin providers (linked activities are
automatically deduplicated).
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# ── Constants ────────────────────────────────────────────────────────
ATL_DAYS = 7  # Acute Training Load time constant (fatigue)
CTL_DAYS = 42  # Chronic Training Load time constant (fitness)
DEFAULT_MAX_HR = 190  # Fallback if no observed max HR
DEFAULT_REST_HR = 60  # Fallback resting heart rate


# ── Heart rate helpers ───────────────────────────────────────────────

def estimate_max_hr(session: Session) -> int:
    """Return the highest observed max heart rate across all activities.

    Falls back to *DEFAULT_MAX_HR* when no activity has HR data.
    """
    from sqlalchemy import func

    from openactivity.db.models import Activity

    result = session.query(func.max(Activity.max_heartrate)).scalar()
    return int(result) if result else DEFAULT_MAX_HR


def estimate_rest_hr(session: Session) -> int:
    """Estimate resting HR from the lowest observed average HR.

    Only considers activities longer than 20 minutes to avoid warm-ups.
    Falls back to *DEFAULT_REST_HR*.
    """
    from sqlalchemy import func

    from openactivity.db.models import Activity

    result = (
        session.query(func.min(Activity.average_heartrate))
        .filter(
            Activity.average_heartrate.isnot(None),
            Activity.moving_time > 1200,  # > 20 min
        )
        .scalar()
    )
    if result and result > 40:
        return int(result)
    return DEFAULT_REST_HR


# ── TSS computation ──────────────────────────────────────────────────

def compute_tss(
    average_hr: float,
    moving_time_seconds: int,
    max_hr: int,
    rest_hr: int,
) -> float | None:
    """Compute TRIMP-based Training Stress Score for an activity.

    Uses the exponentially-weighted TRIMP formula::

        hr_ratio  = (avg_hr - rest_hr) / (max_hr - rest_hr)
        TRIMP     = duration_min × hr_ratio × 0.64 × e^(1.92 × hr_ratio)

    The result is scaled so that a 60-minute effort at lactate threshold
    (~88 % of max HR) yields approximately 100 TSS.

    Returns *None* when the input data is insufficient.
    """
    if not average_hr or not moving_time_seconds or max_hr <= rest_hr:
        return None

    if average_hr <= rest_hr:
        return 0.0

    hr_ratio = (average_hr - rest_hr) / (max_hr - rest_hr)
    hr_ratio = min(hr_ratio, 1.0)  # clamp

    duration_min = moving_time_seconds / 60.0
    trimp = duration_min * hr_ratio * 0.64 * math.exp(1.92 * hr_ratio)

    # Normalise: a 60-min threshold effort (hr_ratio ≈ 0.88) → ~100 TSS
    threshold_ratio = 0.88
    reference_trimp = 60.0 * threshold_ratio * 0.64 * math.exp(1.92 * threshold_ratio)
    tss = trimp * (100.0 / reference_trimp) if reference_trimp > 0 else trimp

    return round(tss, 1)


def compute_activity_tss(activity, max_hr: int, rest_hr: int) -> float | None:
    """Convenience wrapper: compute TSS for an Activity ORM object."""
    if not activity.average_heartrate or not activity.moving_time:
        return None
    return compute_tss(activity.average_heartrate, activity.moving_time, max_hr, rest_hr)


# ── Daily aggregation ────────────────────────────────────────────────

def compute_daily_tss(
    session: Session,
    *,
    after: datetime | None = None,
    before: datetime | None = None,
    activity_type: str | None = None,
) -> tuple[dict[date, float], dict]:
    """Query activities, compute per-activity TSS, aggregate by day.

    Returns
    -------
    daily_tss : dict[date, float]
        Mapping of calendar date → total TSS for that day.
    meta : dict
        Metadata: max_hr, rest_hr, activities_with_hr, activities_without_hr.
    """
    from openactivity.db.queries import get_activities

    max_hr = estimate_max_hr(session)
    rest_hr = estimate_rest_hr(session)

    # Fetch all activities in the range (dedup is handled by get_activities)
    activities = get_activities(
        session,
        after=after,
        before=before,
        activity_type=activity_type,
        sort="date",
        limit=100_000,
        offset=0,
    )

    daily_tss: dict[date, float] = {}
    with_hr = 0
    without_hr = 0

    for activity in activities:
        tss = compute_activity_tss(activity, max_hr, rest_hr)
        if tss is None:
            without_hr += 1
            continue

        with_hr += 1
        day = activity.start_date.date() if activity.start_date else None
        if day is None:
            continue

        daily_tss[day] = daily_tss.get(day, 0.0) + tss

    meta = {
        "max_hr": max_hr,
        "rest_hr": rest_hr,
        "activities_with_hr": with_hr,
        "activities_without_hr": without_hr,
    }
    return daily_tss, meta


# ── ATL / CTL / TSB computation ──────────────────────────────────────

def compute_fitness_fatigue(
    daily_tss: dict[date, float],
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    """Run the exponential decay model over daily TSS values.

    Returns a list of dicts, one per day, with keys:
    ``date``, ``tss``, ``atl``, ``ctl``, ``tsb``.
    """
    if not daily_tss:
        return []

    all_dates = sorted(daily_tss.keys())
    start = start_date or all_dates[0]
    end = end_date or date.today()

    atl = 0.0
    ctl = 0.0
    results = []
    current = start

    while current <= end:
        tss = daily_tss.get(current, 0.0)
        atl = atl + (tss - atl) / ATL_DAYS
        ctl = ctl + (tss - ctl) / CTL_DAYS
        tsb = ctl - atl

        results.append({
            "date": current.isoformat(),
            "tss": round(tss, 1),
            "atl": round(atl, 1),
            "ctl": round(ctl, 1),
            "tsb": round(tsb, 1),
        })
        current += timedelta(days=1)

    return results


# ── Status classification ────────────────────────────────────────────

def classify_status(daily_data: list[dict]) -> str:
    """Classify current training status from the daily series.

    Uses the last entry's TSB and the CTL change over the past 14 days.
    """
    if not daily_data:
        return "unknown"

    current = daily_data[-1]
    tsb = current["tsb"]
    ctl_now = current["ctl"]

    # Find CTL from 14 days ago
    ctl_14d_ago = ctl_now
    if len(daily_data) > 14:
        ctl_14d_ago = daily_data[-15]["ctl"]

    ctl_change = ctl_now - ctl_14d_ago

    if ctl_change > 2 and tsb > 5:
        return "peaking"
    if ctl_change > 2 and tsb < -15:
        return "overreaching"
    if ctl_change < -5 and tsb > 5:
        return "detraining"
    return "maintaining"


# ── Orchestrator ─────────────────────────────────────────────────────

def analyze_fitness(
    session: Session,
    *,
    last: str = "6m",
    activity_type: str | None = None,
) -> dict:
    """Full fitness/fatigue analysis.  Returns a result dict matching the
    CLI contract in ``contracts/cli-commands.md``.
    """
    after = _parse_time_window(last)

    daily_tss, meta = compute_daily_tss(
        session,
        after=after,
        activity_type=activity_type,
    )

    if not daily_tss:
        return {"error": "no_hr_data", "meta": meta}

    # We need data from before the window to seed ATL/CTL, so start
    # the model from the earliest available data.
    start_date = min(daily_tss.keys())
    daily_data = compute_fitness_fatigue(daily_tss, start_date=start_date)

    if not daily_data:
        return {"error": "no_data", "meta": meta}

    status = classify_status(daily_data)
    current = daily_data[-1]

    # CTL 14 days ago for trend
    ctl_14d_ago = daily_data[-15]["ctl"] if len(daily_data) > 14 else daily_data[0]["ctl"]

    # Filter daily data to the requested window for output
    if after:
        after_date = after.date() if isinstance(after, datetime) else after
        daily_data = [d for d in daily_data if d["date"] >= after_date.isoformat()]

    return {
        "status": status,
        "current": {
            "ctl": current["ctl"],
            "atl": current["atl"],
            "tsb": current["tsb"],
            "ctl_14d_ago": ctl_14d_ago,
            "ctl_change": round(current["ctl"] - ctl_14d_ago, 1),
        },
        "meta": {
            "activities_with_hr": meta["activities_with_hr"],
            "activities_without_hr": meta["activities_without_hr"],
            "max_hr": meta["max_hr"],
            "rest_hr": meta["rest_hr"],
            "time_range_start": daily_data[0]["date"] if daily_data else None,
            "time_range_end": daily_data[-1]["date"] if daily_data else None,
            "activity_type_filter": activity_type,
        },
        "daily": daily_data,
    }


# ── Chart generation ─────────────────────────────────────────────────

def generate_fitness_chart(daily_data: list[dict], output_path: str) -> str:
    """Generate a fitness / fatigue / form chart as PNG.

    Returns the absolute path to the written file.
    """
    import matplotlib

    matplotlib.use("Agg")  # non-interactive backend
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    dates = [datetime.fromisoformat(d["date"]) for d in daily_data]
    ctls = [d["ctl"] for d in daily_data]
    atls = [d["atl"] for d in daily_data]
    tsbs = [d["tsb"] for d in daily_data]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(dates, ctls, color="#2196F3", linewidth=2, label="Fitness (CTL)")
    ax.plot(dates, atls, color="#F44336", linewidth=2, label="Fatigue (ATL)")
    ax.plot(dates, tsbs, color="#4CAF50", linewidth=1.5, linestyle="--", label="Form (TSB)")
    ax.axhline(y=0, color="gray", linewidth=0.8, linestyle=":")

    ax.fill_between(dates, tsbs, 0, alpha=0.1, color="#4CAF50")

    ax.set_title("Fitness / Fatigue / Form", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Training Load")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    fig.autofmt_xdate()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)

    return output_path


# ── Time window parser (shared pattern) ──────────────────────────────

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
