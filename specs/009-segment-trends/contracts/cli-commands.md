# CLI Command Contracts: Segment Trend Analysis

## Command: `openactivity strava segment <ID> trend`

**Purpose**: Show performance trend analysis for a specific segment.

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| segment_id | Integer | Yes | — | Strava segment ID |

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| --json | Boolean | false | Global flag: output as JSON |

### Human Output

```
Segment Trend: Morning Hill Loop (#12345)
Distance: 1.2 km | Efforts: 12 | Period: Jan 2025 – Mar 2026

Trend: ↑ Improving (-3.2 sec/month, R²=0.78)

  Best:   4:12 (2026-03-15)
  Worst:  5:01 (2025-01-20)
  Recent: 4:18 (2026-03-20) [+6s from best]

HR-Adjusted Trend: ↑ Improving (-0.02/month, R²=0.65)
  Based on 9 of 12 efforts with HR data

Effort History:
  Date        Time    Avg HR   Δ Best
  2025-01-20  5:01    152      +49s
  2025-02-14  4:48    148      +36s
  ...
  2026-03-20  4:18    155      +6s
```

### JSON Output

```json
{
  "segment_id": 12345,
  "segment_name": "Morning Hill Loop",
  "distance": 1200.0,
  "effort_count": 12,
  "trend": {
    "direction": "improving",
    "rate_of_change": -3.2,
    "rate_unit": "seconds/month",
    "r_squared": 0.78
  },
  "best_effort": {
    "date": "2026-03-15",
    "elapsed_time": 252,
    "average_heartrate": 158
  },
  "worst_effort": {
    "date": "2025-01-20",
    "elapsed_time": 301,
    "average_heartrate": 152
  },
  "recent_effort": {
    "date": "2026-03-20",
    "elapsed_time": 258,
    "average_heartrate": 155,
    "delta_from_best": 6
  },
  "hr_adjusted": {
    "direction": "improving",
    "rate_of_change": -0.02,
    "rate_unit": "normalized_units/month",
    "r_squared": 0.65,
    "effort_count": 9
  },
  "efforts": [
    {
      "date": "2025-01-20",
      "elapsed_time": 301,
      "average_heartrate": 152,
      "delta_from_best": 49,
      "hr_normalized_time": 1.98
    }
  ]
}
```

### Error Cases

| Condition | Human Output | JSON Output |
|-----------|-------------|-------------|
| Segment not in local DB | "Segment 99999 not found. Run `openactivity strava sync` to fetch segment data." | `{"error": "segment_not_found", "message": "..."}` |
| No efforts for segment | "No efforts found for segment 12345. Run `openactivity strava sync` to fetch effort data." | `{"error": "no_efforts", "message": "..."}` |
| < 3 efforts | Shows efforts but: "Need at least 3 efforts for trend analysis. You have N." | `{"error": "insufficient_efforts", "efforts": [...]}` |

---

## Command: `openactivity strava segments list` (enhanced)

**Purpose**: List starred segments with trend indicators added.

### Existing columns preserved, new columns added:

| Column | New? | Description |
|--------|------|-------------|
| ID | No | Segment ID |
| Name | No | Segment name |
| Type | No | Activity type |
| Distance | No | Distance |
| Grade | No | Average grade |
| PR Time | No | Personal record |
| Efforts | No | Effort count |
| **Trend** | **Yes** | ↑/↓/→ or — |
| **Rate** | **Yes** | sec/month or — |

### Trend Indicators

| Indicator | Meaning | Condition |
|-----------|---------|-----------|
| ↑ | Improving | slope < -1 sec/month |
| ↓ | Declining | slope > +1 sec/month |
| → | Stable | slope within ±1 sec/month |
| — | Insufficient data | < 3 efforts |
