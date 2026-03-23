# Data Model: Race Predictor & Readiness Score

**Note**: All entities are computed on-the-fly. No new database tables or schema changes.

## Computed Entities

### ReferenceEffort

A user's best effort at a known distance, used as input to the Riegel formula.

| Field | Type | Description |
|-------|------|-------------|
| distance_meters | float | Standard distance in meters (e.g., 5000.0 for 5K) |
| distance_label | str | Human-readable label (e.g., "5K", "Half Marathon") |
| time_seconds | float | Best effort time in seconds |
| pace_per_km | float | Pace in seconds per km |
| activity_id | int | Source activity ID |
| activity_date | datetime | Date of the effort |
| days_ago | int | Days since effort (for recency scoring) |

**Source**: Queried from `PersonalRecord` table via `get_personal_records()` or computed on-the-fly via `find_best_effort_for_distance()`.

### Prediction

The computed race prediction for a target distance.

| Field | Type | Description |
|-------|------|-------------|
| target_distance | float | Target distance in meters |
| target_label | str | Human-readable label (e.g., "10K") |
| predicted_time | float | Predicted finish time in seconds |
| predicted_pace | float | Predicted pace in seconds per km |
| confidence_low | float | Lower bound of confidence interval (seconds) |
| confidence_high | float | Upper bound of confidence interval (seconds) |
| confidence_pct | float | Confidence interval width as % of prediction |
| reference_efforts | list[ReferenceEffort] | Efforts used for prediction |
| prediction_source | str | "multi" (averaged) or "single" (one reference) |

**Computed from**: Riegel formula applied to each ReferenceEffort, then averaged.

### ReadinessScore

Composite fitness assessment for race readiness.

| Field | Type | Description |
|-------|------|-------------|
| overall | int | Overall readiness score 0-100 |
| label | str | "Not Ready" / "Building" / "Almost Ready" / "Race Ready" |
| consistency | ComponentScore | Training consistency component |
| volume_trend | ComponentScore | Volume trend component |
| taper_status | ComponentScore | Taper detection component |
| pr_recency | ComponentScore | PR recency component |

### ComponentScore

Individual readiness component.

| Field | Type | Description |
|-------|------|-------------|
| score | int | Component score 0-100 |
| weight | float | Weight in overall calculation (0.20-0.30) |
| description | str | Human-readable explanation of the score |

### PredictResult

Top-level result returned by the orchestration function.

| Field | Type | Description |
|-------|------|-------------|
| target_distance | str | Requested distance label |
| prediction | Prediction | Race time prediction |
| readiness | ReadinessScore | Readiness assessment |
| race_date | str or None | Optional race date |
| days_until_race | int or None | Days until race (if date provided) |
| current_phase | str | Current training phase from blocks system |
| activity_type | str | Activity type filter used |

## Relationships

```
PredictResult
├── Prediction
│   └── ReferenceEffort[] (from PersonalRecord or on-the-fly scan)
├── ReadinessScore
│   ├── ComponentScore (consistency — from aggregate_weeks)
│   ├── ComponentScore (volume_trend — from aggregate_weeks)
│   ├── ComponentScore (taper_status — from aggregate_weeks + classify_weeks)
│   └── ComponentScore (pr_recency — from PersonalRecord dates)
└── current_phase (from detect_blocks)
```

## Reused Models (no changes)

- **Activity** (`db/models.py`): Source of training data — distance, time, HR, speed, date
- **PersonalRecord** (`db/models.py`): Source of best efforts — distance_type, value, achieved_date, is_current
- **WeekSummary** (computed in `analysis/blocks.py`): Weekly aggregation for readiness components
