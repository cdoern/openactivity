# CLI Contract: Race Predictor

## Command: `openactivity strava predict`

### Synopsis

```
openactivity strava predict --distance <DISTANCE> [--race-date YYYY-MM-DD] [--type TYPE]
openactivity --json strava predict --distance <DISTANCE>
```

### Flags

| Flag | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `--distance` | string | — | Yes | Target distance: `1mi`, `5K`, `10K`, `half`, `marathon` |
| `--race-date` | string | None | No | Race date in YYYY-MM-DD format (must be in the future) |
| `--type` | string | `Run` | No | Activity type filter (case-insensitive) |

### Human-Readable Output

```
Race Prediction: 10K

  Predicted Time:  42:30
  Predicted Pace:  4:15/km
  Confidence:      41:45 — 43:15 (±1.8%)

Reference Efforts:
  5K       20:15    2026-03-10    (12 days ago)
  1mi       5:48    2026-02-28    (22 days ago)
  Half   1:35:20    2026-01-15    (66 days ago)

Readiness Score: 78/100 — Almost Ready

  Consistency    ████████░░  82  (7/8 weeks with 3+ activities)
  Volume Trend   ███████░░░  72  (volume steady vs prior 4 weeks)
  Taper Status   ████████░░  80  (volume declining, intensity maintained)
  PR Recency     ███████░░░  74  (most recent PR: 12 days ago)

Current Phase: Build — Rising volume and intensity
```

With `--race-date`:
```
Race Date: 2026-06-15 (85 days away)
Training Phase: Build — consider beginning taper 3-4 weeks before race
```

### JSON Output

```json
{
  "target_distance": "10K",
  "target_distance_meters": 10000.0,
  "activity_type": "Run",
  "prediction": {
    "predicted_time_seconds": 2550,
    "predicted_time_formatted": "42:30",
    "predicted_pace_seconds": 255,
    "predicted_pace_formatted": "4:15/km",
    "confidence_low_seconds": 2505,
    "confidence_high_seconds": 2595,
    "confidence_low_formatted": "41:45",
    "confidence_high_formatted": "43:15",
    "confidence_pct": 1.8,
    "prediction_source": "multi"
  },
  "reference_efforts": [
    {
      "distance_label": "5K",
      "distance_meters": 5000.0,
      "time_seconds": 1215,
      "time_formatted": "20:15",
      "pace_formatted": "4:03/km",
      "activity_date": "2026-03-10",
      "days_ago": 12
    }
  ],
  "readiness": {
    "overall": 78,
    "label": "Almost Ready",
    "components": {
      "consistency": {"score": 82, "weight": 0.30, "description": "7/8 weeks with 3+ activities"},
      "volume_trend": {"score": 72, "weight": 0.25, "description": "volume steady vs prior 4 weeks"},
      "taper_status": {"score": 80, "weight": 0.25, "description": "volume declining, intensity maintained"},
      "pr_recency": {"score": 74, "weight": 0.20, "description": "most recent PR: 12 days ago"}
    }
  },
  "race_date": "2026-06-15",
  "days_until_race": 85,
  "current_phase": "build",
  "current_phase_description": "Rising volume and intensity — preparing for performance"
}
```

### Error Output (insufficient data)

```
Not enough data to predict 10K.

  Need at least 2 best efforts at different distances.
  Found: 1 (5K only)

  Tip: Run more races or time trials at varied distances,
  then sync with `openactivity strava sync`.
```

### Error JSON

```json
{
  "error": "insufficient_data",
  "message": "Need at least 2 best efforts at different distances. Found 1.",
  "target_distance": "10K",
  "efforts_found": 1
}
```
