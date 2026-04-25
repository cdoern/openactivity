"""Daily recovery & readiness score.

Combines Garmin health metrics (HRV, sleep) with training load (TSB,
volume trend) to produce a single 0-100 readiness score with an
actionable recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# ── Component weights ──────────────��────────────────────────────────
HRV_WEIGHT = 0.30
SLEEP_WEIGHT = 0.20
FORM_WEIGHT = 0.30
VOLUME_WEIGHT = 0.20

# ── TSB-to-score thresholds ──────────────────���──────────────────────
TSB_THRESHOLDS = [
    (15, 90),    # >= 15 → 90
    (5, 70),     # >= 5  → 70
    (-10, 50),   # >= -10 → 50
    (-20, 30),   # >= -20 → 30
]
TSB_FLOOR_SCORE = 10

# ── Recommendation labels ──────��────────────────────────────────────
LABELS = [
    (75, "Go Hard", "Body is recovered — good day to push intensity or do a quality workout."),
    (40, "Easy Day", "Moderate recovery — keep effort easy or do cross-training."),
    (0, "Rest", "Take a rest day or very easy activity to allow recovery."),
]


@dataclass
class ComponentScore:
    """A single scored component of the readiness model."""

    name: str
    score: int
    weight: float
    available: bool
    description: str


@dataclass
class ReadinessResult:
    """Result of a daily readiness computation."""

    date: date
    score: int
    label: str
    recommendation: str
    components: list[ComponentScore] = field(default_factory=list)


# ── Component scorers ───────────────��───────────────────────────────


def compute_hrv_score(session: Session, target_date: date) -> ComponentScore:
    """Score HRV relative to 7-day baseline.

    Queries 8 days of GarminDailySummary (7 prior days + target day).
    Compares today's hrv_avg to the 7-day rolling average.
    """
    from openactivity.db.queries import get_daily_summaries

    baseline_start = target_date - timedelta(days=7)
    summaries = get_daily_summaries(
        session, after=baseline_start, before=target_date
    )

    # Find today's HRV
    today_hrv = None
    baseline_values = []

    for s in summaries:
        if s.hrv_avg is not None:
            if s.date == target_date:
                today_hrv = s.hrv_avg
            else:
                baseline_values.append(s.hrv_avg)

    if today_hrv is None:
        return ComponentScore(
            name="hrv",
            score=0,
            weight=HRV_WEIGHT,
            available=False,
            description="HRV data unavailable",
        )

    if not baseline_values:
        # Have today but no baseline — score at neutral
        return ComponentScore(
            name="hrv",
            score=50,
            weight=HRV_WEIGHT,
            available=True,
            description=f"HRV {today_hrv}ms (no baseline yet)",
        )

    baseline_avg = sum(baseline_values) / len(baseline_values)

    if baseline_avg <= 0:
        score = 50
    else:
        # Ratio-based scoring: HRV at baseline = 70, 15%+ above = 90, 15%+ below = 40
        ratio = today_hrv / baseline_avg
        if ratio >= 1.15:
            score = 90
        elif ratio >= 1.0:
            # Linear 70-90
            score = int(70 + (ratio - 1.0) / 0.15 * 20)
        elif ratio >= 0.85:
            # Linear 40-70
            score = int(40 + (ratio - 0.85) / 0.15 * 30)
        else:
            # Linear 10-40
            score = max(10, int(40 - (0.85 - ratio) / 0.15 * 30))

    # Optional: adjust with Body Battery and stress
    today_summary = None
    for s in summaries:
        if s.date == target_date:
            today_summary = s
            break

    if today_summary:
        if today_summary.body_battery_max is not None:
            # Body Battery 0-100: high = good
            bb_mod = (today_summary.body_battery_max - 50) / 100  # -0.5 to +0.5
            score = max(10, min(100, int(score + bb_mod * 10)))
        if today_summary.stress_avg is not None:
            # Stress 0-100: high = bad
            stress_mod = (50 - today_summary.stress_avg) / 100  # -0.5 to +0.5
            score = max(10, min(100, int(score + stress_mod * 10)))

    diff = today_hrv - baseline_avg
    direction = "above" if diff >= 0 else "below"
    desc = f"HRV {today_hrv}ms vs {baseline_avg:.0f}ms baseline — {direction} average"

    return ComponentScore(
        name="hrv",
        score=max(0, min(100, score)),
        weight=HRV_WEIGHT,
        available=True,
        description=desc,
    )


def compute_sleep_score(session: Session, target_date: date) -> ComponentScore:
    """Score sleep quality from Garmin sleep_score."""
    from openactivity.db.queries import get_daily_summary

    summary = get_daily_summary(session, target_date)

    if not summary or summary.sleep_score is None:
        return ComponentScore(
            name="sleep",
            score=0,
            weight=SLEEP_WEIGHT,
            available=False,
            description="Sleep data unavailable",
        )

    # Garmin sleep_score is already 0-100
    score = max(0, min(100, summary.sleep_score))

    return ComponentScore(
        name="sleep",
        score=score,
        weight=SLEEP_WEIGHT,
        available=True,
        description=f"Sleep score: {summary.sleep_score}/100",
    )


def compute_form_score(session: Session, target_date: date) -> ComponentScore:
    """Score training form from TSB (Training Stress Balance)."""
    from openactivity.analysis.fitness import compute_daily_tss, compute_fitness_fatigue

    daily_tss, _meta = compute_daily_tss(session)

    if not daily_tss:
        return ComponentScore(
            name="form",
            score=0,
            weight=FORM_WEIGHT,
            available=False,
            description="No training data with HR for TSB computation",
        )

    daily_data = compute_fitness_fatigue(daily_tss)

    if not daily_data:
        return ComponentScore(
            name="form",
            score=0,
            weight=FORM_WEIGHT,
            available=False,
            description="Insufficient data for TSB computation",
        )

    # Find TSB for target date
    target_iso = target_date.isoformat()
    tsb = None
    for entry in reversed(daily_data):
        if entry["date"] <= target_iso:
            tsb = entry["tsb"]
            break

    if tsb is None:
        return ComponentScore(
            name="form",
            score=50,
            weight=FORM_WEIGHT,
            available=True,
            description="TSB: no data for target date",
        )

    # Map TSB to score using piecewise thresholds
    score = TSB_FLOOR_SCORE
    for threshold, threshold_score in TSB_THRESHOLDS:
        if tsb >= threshold:
            score = threshold_score
            break

    # Interpolate within ranges for smoother scores
    if tsb >= 15:
        score = min(100, 90 + int((tsb - 15) * 0.5))
    elif tsb >= 5:
        score = 70 + int((tsb - 5) / 10 * 20)
    elif tsb >= -10:
        score = 50 + int((tsb + 10) / 15 * 20)
    elif tsb >= -20:
        score = 30 + int((tsb + 20) / 10 * 20)
    else:
        score = max(10, 30 + int((tsb + 20) / 10 * 20))

    score = max(0, min(100, score))

    if tsb > 5:
        freshness = "fresh"
    elif tsb > -10:
        freshness = "neutral"
    else:
        freshness = "fatigued"

    return ComponentScore(
        name="form",
        score=score,
        weight=FORM_WEIGHT,
        available=True,
        description=f"TSB: {tsb:+.1f} — {freshness}",
    )


def compute_volume_score(session: Session, target_date: date) -> ComponentScore:
    """Score volume trend: last 7 days vs prior 7 days."""
    from openactivity.db.queries import get_activities

    end = datetime.combine(target_date, datetime.max.time())
    mid = end - timedelta(days=7)
    start = end - timedelta(days=14)

    recent_activities = get_activities(
        session, after=mid, before=end, sort="date", limit=10000, offset=0
    )
    prior_activities = get_activities(
        session, after=start, before=mid, sort="date", limit=10000, offset=0
    )

    recent_dist = sum(a.distance or 0 for a in recent_activities)
    prior_dist = sum(a.distance or 0 for a in prior_activities)

    if recent_dist == 0 and prior_dist == 0:
        return ComponentScore(
            name="volume",
            score=0,
            weight=VOLUME_WEIGHT,
            available=False,
            description="No recent training data",
        )

    if prior_dist <= 0:
        # First week of training — score neutral
        return ComponentScore(
            name="volume",
            score=60,
            weight=VOLUME_WEIGHT,
            available=True,
            description="First week of data — no prior reference",
        )

    ratio = recent_dist / prior_dist

    # Score based on ratio:
    # 0.7-1.0 (slight taper to stable) → 80-90
    # 1.0-1.1 (slight increase) → 70-80
    # 1.1-1.3 (moderate ramp) → 50-70
    # >1.3 (sharp spike — injury risk) → 20-50
    # <0.5 (sharp drop — detraining) → 40-60
    # 0.5-0.7 (moderate reduction) → 60-80
    if 0.7 <= ratio <= 1.0:
        score = 80 + int((1.0 - ratio) / 0.3 * 10)
    elif 1.0 < ratio <= 1.1:
        score = 70 + int((1.1 - ratio) / 0.1 * 10)
    elif 1.1 < ratio <= 1.3:
        score = 50 + int((1.3 - ratio) / 0.2 * 20)
    elif ratio > 1.3:
        score = max(20, 50 - int((ratio - 1.3) / 0.3 * 30))
    elif 0.5 <= ratio < 0.7:
        score = 60 + int((ratio - 0.5) / 0.2 * 20)
    else:  # < 0.5
        score = max(40, 60 - int((0.5 - ratio) / 0.5 * 20))

    score = max(0, min(100, score))

    if ratio > 1.3:
        trend = "sharp ramp — injury risk"
    elif ratio > 1.1:
        trend = "moderate increase"
    elif ratio >= 0.9:
        trend = "stable"
    elif ratio >= 0.7:
        trend = "slight taper"
    else:
        trend = "significant reduction"

    return ComponentScore(
        name="volume",
        score=score,
        weight=VOLUME_WEIGHT,
        available=True,
        description=f"7d volume {trend} vs prior 7d",
    )


# ── Orchestrator ───────────────���────────────────────────────────────


def classify_readiness(score: int) -> tuple[str, str]:
    """Map composite score to label and recommendation."""
    for threshold, label, rec in LABELS:
        if score >= threshold:
            return label, rec
    return LABELS[-1][1], LABELS[-1][2]


def compute_readiness(session: Session, target_date: date | None = None) -> ReadinessResult:
    """Compute daily readiness score for a given date.

    Calls all four component scorers, handles missing data with
    proportional weight redistribution, computes composite score.
    """
    if target_date is None:
        target_date = date.today()

    components = [
        compute_hrv_score(session, target_date),
        compute_sleep_score(session, target_date),
        compute_form_score(session, target_date),
        compute_volume_score(session, target_date),
    ]

    # Redistribute weights for unavailable components
    available = [c for c in components if c.available]

    if not available:
        return ReadinessResult(
            date=target_date,
            score=0,
            label="Unknown",
            recommendation="No data available. Import Garmin data or sync Strava activities first.",
            components=components,
        )

    total_available_weight = sum(c.weight for c in available)
    for c in available:
        c.weight = c.weight / total_available_weight  # Normalize to sum to 1.0

    composite = sum(c.score * c.weight for c in available)
    score = max(0, min(100, round(composite)))

    label, recommendation = classify_readiness(score)

    return ReadinessResult(
        date=target_date,
        score=score,
        label=label,
        recommendation=recommendation,
        components=components,
    )


def compute_readiness_trend(
    session: Session,
    days: int,
) -> dict:
    """Compute readiness scores for each day in the window.

    Returns dict with 'today', 'daily' list, and 'summary' stats.
    """
    today = date.today()
    start = today - timedelta(days=days - 1)

    daily = []
    current = start
    while current <= today:
        result = compute_readiness(session, current)
        daily.append(result)
        current += timedelta(days=1)

    scores = [r.score for r in daily if r.score > 0]
    avg = round(sum(scores) / len(scores)) if scores else 0
    best = max(daily, key=lambda r: r.score) if daily else None
    worst = min(daily, key=lambda r: r.score) if daily else None

    today_result = compute_readiness(session, today)

    return {
        "today": today_result,
        "daily": daily,
        "summary": {
            "average": avg,
            "best": {"date": best.date.isoformat(), "score": best.score} if best else None,
            "worst": {"date": worst.date.isoformat(), "score": worst.score} if worst else None,
        },
    }
