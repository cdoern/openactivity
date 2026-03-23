# CLI Commands: Grade-Adjusted Pace & Effort Scoring

## Modified Command: `openactivity strava activity <ID>`

### Changes to Activity Detail View

**New fields in summary section** (after existing Pace line):
```
  GAP: 7:15 /mi   (grade-adjusted)
```

**New column in laps table**: GAP column added alongside existing Pace column.

**JSON output additions**:
```json
{
  "gap": 4.47,
  "gap_formatted": "7:15 /mi",
  "gap_available": true,
  "laps": [
    {
      "index": 1,
      "gap": 4.32,
      "gap_formatted": "7:28 /mi",
      ...existing fields...
    }
  ]
}
```

When GAP is unavailable (no elevation stream):
```json
{
  "gap": null,
  "gap_formatted": null,
  "gap_available": false
}
```

---

## New Command: `openactivity strava analyze effort`

### Usage
```
openactivity strava analyze effort [OPTIONS]
```

### Options
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--last` | string | `"90d"` | Time window: "30d", "90d", "6m", "1y", "all" |
| `--type` | string | `"Run"` | Activity type filter |

### Table Output
```
                    Effort Trend (Run, last 90d)
┏━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┓
┃ Date       ┃ Activity ┃  Distance ┃   Pace  ┃     GAP  ┃ Elev.   ┃ Effort ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━┩
│ 2026-03-20 │ Hill Rep │   5.2 mi  │ 8:15/mi │ 7:30/mi  │  420 ft │  78    │
│ 2026-03-18 │ Easy 5   │   5.0 mi  │ 8:45/mi │ 8:40/mi  │   85 ft │  45    │
│ ...        │          │           │         │          │         │        │
└────────────┴──────────┴───────────┴─────────┴──────────┴─────────┴────────┘

  Trend: Improving ↓  |  Avg GAP: 7:55/mi  |  Avg Effort: 62
```

### JSON Output
```json
{
  "time_window": "90d",
  "activity_type": "Run",
  "trend": "improving",
  "avg_gap": 4.78,
  "avg_gap_formatted": "7:55 /mi",
  "avg_effort_score": 62,
  "activity_count": 15,
  "activities": [
    {
      "activity_id": 12345,
      "activity_name": "Hill Repeats",
      "date": "2026-03-20T07:30:00",
      "distance": 8368.0,
      "actual_pace": 5.11,
      "actual_pace_formatted": "8:15 /mi",
      "gap": 4.65,
      "gap_formatted": "7:30 /mi",
      "gap_available": true,
      "effort_score": 78,
      "elevation_gain": 128.0,
      "average_heartrate": 162.0
    }
  ]
}
```
