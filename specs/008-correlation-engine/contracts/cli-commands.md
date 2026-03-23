# CLI Contract: Correlation Engine

## Command: `openactivity strava analyze correlate`

### Synopsis

```
openactivity strava analyze correlate --x <METRIC> --y <METRIC> [--lag N] [--last WINDOW] [--type TYPE]
openactivity --json strava analyze correlate --x <METRIC> --y <METRIC>
```

### Flags

| Flag | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `--x` | string | — | Yes | X-axis metric name |
| `--y` | string | — | Yes | Y-axis metric name |
| `--lag` | int | 0 | No | Lag offset in weeks (0, 1, 2, or 4) |
| `--last` | string | `1y` | No | Time window: "6m", "1y", "all" |
| `--type` | string | `Run` | No | Activity type filter |

### Supported Metrics

`weekly_distance`, `weekly_duration`, `weekly_elevation`, `avg_pace`, `avg_hr`, `max_hr`, `activity_count`, `rest_days`, `longest_run`

### Human-Readable Output

```
Correlation: weekly_distance vs avg_pace (lag: 0 weeks)

  Pearson:   r = -0.62  p = 0.003  (moderate, significant)
  Spearman:  ρ = -0.58  p = 0.007  (moderate, significant)

  Strength:  Moderate negative correlation
  Direction: More weekly distance is associated with faster pace
  Samples:   42 usable weeks (of 52 total)

  ⚠ Note: correlation does not imply causation

Data Points (first 10 of 42):
  Week         weekly_distance    avg_pace
  2025-W15          45.2 km      5:12 /km
  2025-W16          38.7 km      5:25 /km
  ...
```

### JSON Output

```json
{
  "x_metric": "weekly_distance",
  "y_metric": "avg_pace",
  "lag": 0,
  "time_window": "1y",
  "activity_type": "Run",
  "pearson_r": -0.62,
  "pearson_p": 0.003,
  "spearman_r": -0.58,
  "spearman_p": 0.007,
  "strength": "moderate",
  "direction": "More weekly distance is associated with faster pace",
  "significant": true,
  "sample_size": 42,
  "total_weeks": 52,
  "data_points": [
    {"week_key": "2025-W15", "x": 45200.0, "y": 312.0},
    {"week_key": "2025-W16", "x": 38700.0, "y": 325.0}
  ]
}
```

### Error Output (insufficient data)

```
Not enough data to compute correlation.

  Need at least 4 weeks with both metrics present.
  Found: 2 usable weeks (of 8 total)

  Tip: Use a wider time window (--last 1y) or ensure
  activities have the required data (e.g., heart rate).
```
