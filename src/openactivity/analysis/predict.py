"""Race prediction and readiness scoring.

Predicts race times using the Riegel formula from personal record best efforts.
Computes a readiness score (0-100) based on training consistency, volume trend,
taper status, and PR recency.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from openactivity.analysis.blocks import (
    aggregate_weeks,
    compute_week_intensity,
    detect_blocks,
)
from openactivity.analysis.records import RUNNING_DISTANCES
from openactivity.db.queries import get_activities, get_personal_records

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Standard distances: label → meters
DISTANCES: dict[str, float] = {label: meters for label, meters in RUNNING_DISTANCES}

# Display-friendly names
DISTANCE_DISPLAY: dict[str, str] = {
    "1mi": "1 Mile",
    "5K": "5K",
    "10K": "10K",
    "half": "Half Marathon",
    "marathon": "Marathon",
}

# Riegel formula exponent
RIEGEL_EXPONENT = 1.06

# Readiness score weights
CONSISTENCY_WEIGHT = 0.30
VOLUME_WEIGHT = 0.25
TAPER_WEIGHT = 0.25
RECENCY_WEIGHT = 0.20

# Readiness labels
READINESS_LABELS = [
    (40, "Not Ready"),
    (60, "Building"),
    (80, "Almost Ready"),
    (100, "Race Ready"),
]

# Confidence interval base percentage
CONFIDENCE_BASE_PCT = 0.02

# Training data requirements
MIN_TRAINING_WEEKS = 4
CONSISTENCY_WINDOW_WEEKS = 8
MIN_ACTIVITIES_PER_WEEK = 3

# Recency thresholds for reference efforts (days)
MAX_EFFORT_AGE_DAYS = 180


def riegel_predict(
    reference_time: float,
    reference_distance: float,
    target_distance: float,
    exponent: float = RIEGEL_EXPONENT,
) -> float:
    """Apply Riegel formula: T2 = T1 * (D2/D1)^exponent.

    Args:
        reference_time: Known effort time in seconds.
        reference_distance: Known effort distance in meters.
        target_distance: Target distance in meters.
        exponent: Riegel exponent (default 1.06).

    Returns:
        Predicted time in seconds.
    """
    return reference_time * (target_distance / reference_distance) ** exponent


def get_reference_efforts(
    session: Session,
    activity_type: str = "Run",
    max_age_days: int = MAX_EFFORT_AGE_DAYS,
) -> list[dict]:
    """Get best efforts at standard distances from PersonalRecord table.

    Args:
        session: Database session.
        activity_type: Activity type filter.
        max_age_days: Maximum age of efforts to consider.

    Returns:
        List of ReferenceEffort dicts sorted by distance.
    """
    records = get_personal_records(session, record_type="distance", current_only=True)
    now = datetime.now()
    efforts = []

    for record in records:
        if record.distance_type not in DISTANCES:
            continue
        if record.value is None or record.value <= 0:
            continue

        days_ago = (now - record.achieved_date).days if record.achieved_date else 999
        distance_meters = DISTANCES[record.distance_type]

        efforts.append({
            "distance_label": record.distance_type,
            "distance_display": DISTANCE_DISPLAY.get(
                record.distance_type, record.distance_type
            ),
            "distance_meters": distance_meters,
            "time_seconds": record.value,
            "pace_per_km": record.value / (distance_meters / 1000),
            "activity_id": record.activity_id,
            "activity_date": record.achieved_date,
            "days_ago": days_ago,
            "is_recent": days_ago <= max_age_days,
        })

    # Sort by distance (shortest first)
    efforts.sort(key=lambda e: e["distance_meters"])
    return efforts


def compute_confidence_interval(
    individual_predictions: list[float],
    reference_efforts: list[dict],
) -> tuple[float, float, float]:
    """Compute confidence interval for a prediction.

    Args:
        individual_predictions: Predicted times from each reference effort.
        reference_efforts: Reference efforts used.

    Returns:
        Tuple of (low_seconds, high_seconds, pct_width).
    """
    if not individual_predictions:
        return 0.0, 0.0, 0.0

    avg_prediction = sum(individual_predictions) / len(individual_predictions)
    pct = CONFIDENCE_BASE_PCT

    # Widen if fewer than 4 reference efforts
    if len(reference_efforts) < 4:
        pct += 0.01 * (4 - len(reference_efforts))

    # Widen if oldest effort is > 90 days
    max_age = max(e["days_ago"] for e in reference_efforts) if reference_efforts else 0
    if max_age > 90:
        pct += 0.01

    # Widen based on spread of predictions
    if len(individual_predictions) > 1:
        spread = max(individual_predictions) - min(individual_predictions)
        spread_pct = spread / avg_prediction if avg_prediction > 0 else 0
        pct += spread_pct / 2

    low = avg_prediction * (1 - pct)
    high = avg_prediction * (1 + pct)
    return low, high, round(pct * 100, 1)


def predict_race_time(
    reference_efforts: list[dict],
    target_distance_meters: float,
) -> dict:
    """Predict race time from reference efforts using Riegel formula.

    Args:
        reference_efforts: List of ReferenceEffort dicts.
        target_distance_meters: Target distance in meters.

    Returns:
        Prediction dict or error dict.
    """
    if not reference_efforts:
        return {
            "error": "no_efforts",
            "message": "No reference efforts available for prediction.",
        }

    # Filter out efforts at the target distance (use others to predict)
    other_efforts = [
        e for e in reference_efforts
        if abs(e["distance_meters"] - target_distance_meters) > 100
    ]

    # If all efforts are at the target distance, use them directly
    if not other_efforts:
        other_efforts = reference_efforts

    # Compute individual predictions from each reference
    predictions = []
    weights = []
    for effort in other_efforts:
        pred = riegel_predict(
            effort["time_seconds"],
            effort["distance_meters"],
            target_distance_meters,
        )
        predictions.append(pred)

        # Weight by recency and distance proximity
        recency_weight = max(0.2, 1.0 - effort["days_ago"] / 365)
        distance_ratio = min(
            effort["distance_meters"], target_distance_meters
        ) / max(effort["distance_meters"], target_distance_meters)
        proximity_weight = distance_ratio ** 0.5
        weights.append(recency_weight * proximity_weight)

    # Weighted average
    total_weight = sum(weights)
    if total_weight > 0:
        predicted_time = sum(
            p * w for p, w in zip(predictions, weights, strict=True)
        ) / total_weight
    else:
        predicted_time = sum(predictions) / len(predictions)

    # Confidence interval
    conf_low, conf_high, conf_pct = compute_confidence_interval(
        predictions, other_efforts
    )

    predicted_pace = predicted_time / (target_distance_meters / 1000)

    return {
        "predicted_time": predicted_time,
        "predicted_pace": predicted_pace,
        "confidence_low": conf_low,
        "confidence_high": conf_high,
        "confidence_pct": conf_pct,
        "reference_efforts": other_efforts,
        "prediction_source": "multi" if len(other_efforts) > 1 else "single",
        "individual_predictions": predictions,
    }


def compute_consistency(
    session: Session,
    activity_type: str = "Run",
    weeks: int = CONSISTENCY_WINDOW_WEEKS,
    provider: str | None = None,
) -> dict:
    """Score training consistency: % of weeks with >= 3 activities.

    Returns:
        ComponentScore dict with score, weight, description.
    """
    after = datetime.now() - timedelta(days=weeks * 7)
    activities = get_activities(
        session, activity_type=activity_type, after=after,
        provider=provider, sort="date", limit=10000, offset=0,
    )
    valid = [a for a in activities if a.distance and a.distance > 0 and a.start_date]

    week_data = aggregate_weeks(valid, after=after)
    if not week_data:
        return {
            "score": 0, "weight": CONSISTENCY_WEIGHT,
            "description": "No training data available",
        }

    active_weeks = sum(
        1 for w in week_data if w["activity_count"] >= MIN_ACTIVITIES_PER_WEEK
    )
    score = min(100, int(active_weeks / weeks * 100))

    return {
        "score": score, "weight": CONSISTENCY_WEIGHT,
        "description": f"{active_weeks}/{weeks} weeks with {MIN_ACTIVITIES_PER_WEEK}+ activities",
    }


def compute_volume_trend(
    session: Session,
    activity_type: str = "Run",
    provider: str | None = None,
) -> dict:
    """Score volume trend: last 4 weeks vs prior 4 weeks.

    Returns:
        ComponentScore dict with score, weight, description.
    """
    after = datetime.now() - timedelta(days=8 * 7)
    activities = get_activities(
        session, activity_type=activity_type, after=after,
        provider=provider, sort="date", limit=10000, offset=0,
    )
    valid = [a for a in activities if a.distance and a.distance > 0 and a.start_date]

    week_data = aggregate_weeks(valid, after=after)
    if len(week_data) < 4:
        return {
            "score": 50, "weight": VOLUME_WEIGHT,
            "description": "Insufficient data for trend analysis",
        }

    # Split into recent 4 and prior 4
    recent = week_data[-4:]
    prior = week_data[:-4] if len(week_data) > 4 else week_data[:len(week_data) // 2]

    recent_vol = sum(w["total_distance"] for w in recent)
    prior_vol = sum(w["total_distance"] for w in prior) if prior else 1.0
    if prior_vol <= 0:
        prior_vol = 1.0

    ratio = recent_vol / prior_vol

    if ratio >= 0.9:
        score = min(100, int(ratio * 80))
        desc = "volume maintained or increasing"
    elif ratio >= 0.7:
        score = 65
        desc = "volume slightly declining"
    else:
        score = max(20, int(ratio * 60))
        desc = "volume significantly declining"

    return {"score": score, "weight": VOLUME_WEIGHT, "description": desc}


def compute_taper_status(
    session: Session,
    activity_type: str = "Run",
    provider: str | None = None,
) -> dict:
    """Score taper status: volume declining with intensity maintained.

    Returns:
        ComponentScore dict with score, weight, description.
    """
    after = datetime.now() - timedelta(days=6 * 7)
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

    week_data = aggregate_weeks(valid, after=after)
    if len(week_data) < 3:
        return {
            "score": 50, "weight": TAPER_WEIGHT,
            "description": "Insufficient data for taper detection",
        }

    # Compute intensity for recent weeks
    pace_distribution = [
        a.average_speed for a in valid
        if a.average_speed and a.average_speed > 0
    ]
    max_hr = max(
        (a.max_heartrate for a in valid if a.max_heartrate and a.max_heartrate > 0),
        default=0,
    )
    estimated_max_hr = max_hr if max_hr > 0 else 190.0

    for week in week_data:
        intensity, source = compute_week_intensity(
            week, estimated_max_hr, pace_distribution
        )
        week["avg_intensity"] = intensity

    recent_3 = week_data[-3:]
    volumes = [w["total_distance"] for w in recent_3]
    intensities = [w["avg_intensity"] for w in recent_3]

    # Detect taper: volume decreasing, intensity maintained (±10%)
    vol_declining = volumes[-1] < volumes[0] * 0.9
    avg_intensity = sum(intensities) / len(intensities) if intensities else 0
    intensity_stable = all(
        abs(i - avg_intensity) < avg_intensity * 0.15 for i in intensities
    ) if avg_intensity > 0 else True

    if vol_declining and intensity_stable:
        score = 85
        desc = "volume declining, intensity maintained — good taper"
    elif vol_declining:
        score = 60
        desc = "volume declining but intensity also dropping"
    elif intensity_stable:
        score = 50
        desc = "volume stable, not yet tapering"
    else:
        score = 40
        desc = "inconsistent volume and intensity pattern"

    return {"score": score, "weight": TAPER_WEIGHT, "description": desc}


def compute_pr_recency(reference_efforts: list[dict]) -> dict:
    """Score PR recency: how recently the user demonstrated speed.

    Args:
        reference_efforts: List of ReferenceEffort dicts.

    Returns:
        ComponentScore dict with score, weight, description.
    """
    if not reference_efforts:
        return {
            "score": 0, "weight": RECENCY_WEIGHT,
            "description": "No personal records found",
        }

    min_days = min(e["days_ago"] for e in reference_efforts)

    if min_days < 14:
        score = 100
    elif min_days < 30:
        score = 85
    elif min_days < 60:
        score = 70
    elif min_days < 90:
        score = 55
    elif min_days < 180:
        score = 40
    else:
        score = 20

    return {
        "score": score, "weight": RECENCY_WEIGHT,
        "description": f"most recent PR: {min_days} days ago",
    }


def compute_readiness_score(
    consistency: dict,
    volume_trend: dict,
    taper_status: dict,
    pr_recency: dict,
) -> dict:
    """Compute overall readiness score from components.

    Returns:
        ReadinessScore dict with overall, label, and components.
    """
    overall = int(
        consistency["score"] * CONSISTENCY_WEIGHT
        + volume_trend["score"] * VOLUME_WEIGHT
        + taper_status["score"] * TAPER_WEIGHT
        + pr_recency["score"] * RECENCY_WEIGHT
    )
    overall = max(0, min(100, overall))

    label = "Not Ready"
    for threshold, lbl in READINESS_LABELS:
        if overall <= threshold:
            label = lbl
            break

    return {
        "overall": overall,
        "label": label,
        "components": {
            "consistency": consistency,
            "volume_trend": volume_trend,
            "taper_status": taper_status,
            "pr_recency": pr_recency,
        },
    }


def predict(
    session: Session,
    *,
    target_distance: str,
    activity_type: str = "Run",
    race_date: str | None = None,
    provider: str | None = None,
) -> dict:
    """Orchestrate race prediction and readiness scoring.

    Args:
        session: Database session.
        target_distance: Distance label (1mi, 5K, 10K, half, marathon).
        activity_type: Activity type filter.
        race_date: Optional race date in YYYY-MM-DD format.

    Returns:
        PredictResult dict with prediction, readiness, and metadata.
    """
    if target_distance not in DISTANCES:
        return {
            "error": "invalid_distance",
            "message": (
                f"Unsupported distance: '{target_distance}'. "
                f"Supported: {', '.join(DISTANCES.keys())}"
            ),
        }

    target_meters = DISTANCES[target_distance]

    # Get reference efforts
    efforts = get_reference_efforts(session, activity_type)

    if len(efforts) < 1:
        return {
            "error": "insufficient_data",
            "message": (
                "No best efforts found. Run `openactivity strava records scan` "
                "to detect personal records from your activities."
            ),
            "target_distance": target_distance,
            "efforts_found": 0,
        }

    # Predict race time
    prediction = predict_race_time(efforts, target_meters)

    if "error" in prediction:
        return prediction

    # Compute readiness if enough training data
    consistency = compute_consistency(session, activity_type, provider=provider)
    volume_trend = compute_volume_trend(session, activity_type, provider=provider)
    taper_status = compute_taper_status(session, activity_type, provider=provider)
    pr_recency = compute_pr_recency(efforts)
    readiness = compute_readiness_score(
        consistency, volume_trend, taper_status, pr_recency
    )

    has_readiness = consistency["score"] > 0

    # Get current training phase
    blocks_result = detect_blocks(
        session, time_window="3m", activity_type=activity_type, provider=provider
    )
    current_phase = blocks_result.get("current_phase", "unknown")
    phase_desc = blocks_result.get("current_phase_description", "")

    # Race date context
    days_until_race = None
    race_date_parsed = None
    if race_date:
        try:
            race_date_parsed = datetime.strptime(race_date, "%Y-%m-%d")
            days_until_race = (race_date_parsed - datetime.now()).days
            if days_until_race < 0:
                return {
                    "error": "past_race_date",
                    "message": f"Race date {race_date} is in the past.",
                }
        except ValueError:
            return {
                "error": "invalid_date",
                "message": f"Invalid date format: '{race_date}'. Use YYYY-MM-DD.",
            }

    # Check for existing PR at target distance
    target_pr = None
    for e in efforts:
        if e["distance_label"] == target_distance:
            target_pr = e
            break

    return {
        "target_distance": target_distance,
        "target_distance_display": DISTANCE_DISPLAY.get(
            target_distance, target_distance
        ),
        "target_distance_meters": target_meters,
        "activity_type": activity_type,
        "prediction": prediction,
        "readiness": readiness if has_readiness else None,
        "target_pr": target_pr,
        "race_date": race_date,
        "days_until_race": days_until_race,
        "current_phase": current_phase,
        "current_phase_description": phase_desc,
    }
