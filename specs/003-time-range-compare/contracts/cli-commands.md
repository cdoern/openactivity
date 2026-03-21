# CLI Command Contract: Custom Time-Range Comparisons

**Branch**: `003-time-range-compare` | **Date**: 2026-03-21

## Command: `openactivity strava analyze compare`

**Description**: Compare training metrics across two arbitrary date ranges.

### Flags

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--range1` | string | Yes | — | First date range in `YYYY-MM-DD:YYYY-MM-DD` format |
| `--range2` | string | Yes | — | Second date range in `YYYY-MM-DD:YYYY-MM-DD` format |
| `--type` | string | No | None (all types) | Filter by activity type (e.g., Run, Ride, Swim) |

Global flags (`--json`, `--units`, `--config`, `--help`) inherited from root.

### Usage Examples

```bash
# Compare Q1 year-over-year
openactivity strava analyze compare \
  --range1 2025-01-01:2025-03-31 \
  --range2 2026-01-01:2026-03-31

# Compare running only
openactivity strava analyze compare \
  --range1 2025-01-01:2025-03-31 \
  --range2 2026-01-01:2026-03-31 \
  --type Run

# JSON output for agent consumption
openactivity strava analyze compare \
  --range1 2025-06-01:2025-08-31 \
  --range2 2026-06-01:2026-08-31 \
  --json
```

### Table Output Format

```
               Training Comparison
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┓
┃ Metric          ┃ Range 1    ┃ Range 2    ┃ Delta   ┃ Change  ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━┩
│ Activities      │         42 │         51 │      +9 │  +21.4% │
│ Distance        │   412.3 km │   498.7 km │ +86.4km │  +21.0% │
│ Moving Time     │   38h 12m  │   45h 33m  │ +7h 21m │  +19.2% │
│ Elevation       │   3,210 m  │   4,105 m  │  +895 m │  +27.9% │
│ Avg Pace        │  5:12/km   │  4:58/km   │ -0:14   │   -4.5% │
│ Avg Heart Rate  │     148 bpm│     145 bpm│    -3   │   -2.0% │
└─────────────────┴────────────┴────────────┴─────────┴─────────┘
  Range 1: 2025-01-01 → 2025-03-31
  Range 2: 2026-01-01 → 2026-03-31
  ⚠ Ranges overlap (if applicable)
```

### JSON Output Schema

```json
{
  "metadata": {
    "range1": {"start": "2025-01-01", "end": "2025-03-31"},
    "range2": {"start": "2026-01-01", "end": "2026-03-31"},
    "activity_type": null,
    "units": "metric",
    "overlap": false
  },
  "range1": {
    "count": 42,
    "distance_m": 412300.0,
    "moving_time_s": 137520,
    "elevation_gain_m": 3210.0,
    "avg_pace_s_per_km": 312.0,
    "avg_heartrate": 148.0
  },
  "range2": {
    "count": 51,
    "distance_m": 498700.0,
    "moving_time_s": 163980,
    "elevation_gain_m": 4105.0,
    "avg_pace_s_per_km": 298.0,
    "avg_heartrate": 145.0
  },
  "deltas": {
    "count": 9,
    "distance_m": 86400.0,
    "moving_time_s": 26460,
    "elevation_gain_m": 895.0,
    "avg_pace_s_per_km": -14.0,
    "avg_heartrate": -3.0
  },
  "pct_changes": {
    "count": 21.4,
    "distance_m": 21.0,
    "moving_time_s": 19.2,
    "elevation_gain_m": 27.9,
    "avg_pace_s_per_km": -4.5,
    "avg_heartrate": -2.0
  }
}
```

### Error Output

```bash
# Missing required flag
$ openactivity strava analyze compare --range1 2025-01-01:2025-03-31
Error: Missing required option '--range2'.

# Invalid date format
$ openactivity strava analyze compare --range1 01-2025:03-2025 --range2 ...
Error: Invalid date format for --range1. Expected YYYY-MM-DD:YYYY-MM-DD.

# Start after end
$ openactivity strava analyze compare --range1 2025-03-31:2025-01-01 --range2 ...
Error: Invalid range for --range1: start date must be before or equal to end date.

# No activities found (not an error — shows zeroes)
$ openactivity strava analyze compare --range1 2020-01-01:2020-01-02 --range2 2020-01-03:2020-01-04 --type Swim
(table with zero values rendered normally)
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (including empty results) |
| 1 | Invalid input (bad date format, missing flags) |
| 2 | No synced data available (database empty or not initialized) |
