# CLI Commands: Training Block / Periodization Detector

## New Command: `openactivity strava analyze blocks`

### Usage
```
openactivity strava analyze blocks [OPTIONS]
```

### Options
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--last` | string | `"6m"` | Time window: "6m", "1y", "all" |
| `--type` | string | `"Run"` | Activity type filter |

### Table Output
```
                Training Blocks (Run, last 6m)
┏━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Phase      ┃ Start      ┃ End        ┃  Weeks ┃  Avg Vol. ┃ Activities ┃ Intensity ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Base       │ 2025-10-06 │ 2025-11-16 │      6 │  22.5 mi  │         18 │        45 │
│ Build      │ 2025-11-17 │ 2025-12-28 │      6 │  28.3 mi  │         22 │        62 │
│ Peak       │ 2025-12-29 │ 2026-01-18 │      3 │  25.1 mi  │         12 │        74 │
│ Recovery   │ 2026-01-19 │ 2026-02-01 │      2 │  12.0 mi  │          6 │        38 │
│ Build ◀    │ 2026-02-02 │ 2026-03-22 │      7 │  30.5 mi  │         28 │        65 │
└────────────┴────────────┴────────────┴────────┴───────────┴────────────┴───────────┘

  Current Phase: Build  |  Total Weeks: 24  |  Activities: 86
```

### JSON Output
```json
{
  "time_window": "6m",
  "activity_type": "Run",
  "current_phase": "build",
  "total_weeks": 24,
  "blocks": [
    {
      "phase": "base",
      "start_date": "2025-10-06",
      "end_date": "2025-11-16",
      "week_count": 6,
      "total_distance": 217000.0,
      "activity_count": 18,
      "avg_weekly_distance": 36166.7,
      "avg_weekly_distance_formatted": "22.5 mi",
      "avg_intensity": 45,
      "is_current": false
    },
    {
      "phase": "build",
      "start_date": "2026-02-02",
      "end_date": "2026-03-22",
      "week_count": 7,
      "total_distance": 343700.0,
      "activity_count": 28,
      "avg_weekly_distance": 49100.0,
      "avg_weekly_distance_formatted": "30.5 mi",
      "avg_intensity": 65,
      "is_current": true
    }
  ]
}
```

When insufficient data (<4 weeks):
```json
{
  "error": "insufficient_data",
  "message": "At least 4 weeks of activity data are needed for block detection. Found 2 weeks.",
  "weeks_found": 2
}
```
