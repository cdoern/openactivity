# CLI Command Contracts: Fitness/Fatigue Model

## `openactivity strava analyze fitness`

Show current fitness (CTL), fatigue (ATL), form (TSB), and training status.

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--last` | string | `6m` | Time range: 30d, 90d, 6m, 1y, all |
| `--type` | string | none | Filter activity type: Run, Ride, Swim |
| `--chart` | bool | false | Generate a fitness chart |
| `--output` | string | fitness_chart.png | Chart output file path |
| `--json` | bool | false | JSON output (global flag) |

### Human Output (default)

```
Fitness / Fatigue / Form

  Status: PEAKING ▲

  Fitness (CTL):   62.3  ▲ +4.1 from 14d ago
  Fatigue (ATL):   55.8
  Form (TSB):       6.5  (fresh)

  Based on 187 activities with HR data (13 skipped, no HR)
  Max HR used: 192 bpm (observed)
  Time range: 2025-09-24 → 2026-03-24 (6 months)

Recent Trend (last 14 days):
┌──────────────┬───────┬───────┬───────┐
│ Date         │   CTL │   ATL │   TSB │
├──────────────┼───────┼───────┼───────┤
│ 2026-03-24   │  62.3 │  55.8 │   6.5 │
│ 2026-03-23   │  61.9 │  58.2 │   3.7 │
│ 2026-03-22   │  61.5 │  54.1 │   7.4 │
│ ...          │       │       │       │
│ 2026-03-10   │  58.2 │  71.3 │ -13.1 │
└──────────────┴───────┴───────┴───────┘
```

### JSON Output

```json
{
  "status": "peaking",
  "current": {
    "ctl": 62.3,
    "atl": 55.8,
    "tsb": 6.5,
    "ctl_14d_ago": 58.2,
    "ctl_change": 4.1
  },
  "meta": {
    "activities_with_hr": 187,
    "activities_without_hr": 13,
    "max_hr": 192,
    "rest_hr": 60,
    "time_range_start": "2025-09-24",
    "time_range_end": "2026-03-24",
    "activity_type_filter": null
  },
  "daily": [
    {
      "date": "2026-03-24",
      "tss": 45.2,
      "ctl": 62.3,
      "atl": 55.8,
      "tsb": 6.5
    }
  ]
}
```

### Chart Output

When `--chart` is used, generates a PNG chart with:
- X axis: dates
- Y axis: load/form values
- Blue line: CTL (Fitness)
- Red line: ATL (Fatigue)
- Green dashed line: TSB (Form)
- Horizontal gray line at TSB=0
- Legend in upper-left
- Title: "Fitness / Fatigue / Form"

### Error Cases

| Condition | Exit Code | Message |
|-----------|-----------|---------|
| No activities in DB | 1 | "No activities found. Run `strava sync` or `garmin import` first." |
| No activities with HR | 1 | "No activities with heart rate data found. TSS requires HR data." |
| Insufficient data (<7 days) | 0 | Shows values with warning: "Less than 7 days of data — ATL may not be reliable." |
| Chart without matplotlib | 1 | "Chart generation requires matplotlib. Install with: pip install matplotlib" |

## Activity Detail TSS (extension to existing `openactivity activity <ID>`)

When an activity has HR data, the detail view includes:

```
  TSS: 78.4
```

JSON output adds:
```json
{
  "tss": 78.4
}
```
