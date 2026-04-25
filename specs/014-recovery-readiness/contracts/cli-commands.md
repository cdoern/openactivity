# CLI Commands Contract: Recovery & Readiness Score

## `openactivity analyze readiness`

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--last` | string | (today only) | Time window: "7d", "30d", "90d" |
| `--provider` | string | None (all) | Filter by provider |

### Human Output (default)

**Today only** (no `--last`):
```
Readiness Score: 72/100 — Easy Day

  HRV         ████████░░  78  (HRV 52ms vs 48ms baseline — above average)
  Sleep       ██████░░░░  62  (Sleep score: 62/100)
  Form        ████████░░  80  (TSB: +8.2 — fresh)
  Volume      ███████░░░  68  (7d volume stable vs prior 7d)

  Recommendation: Good day for an easy aerobic run or cross-training.
```

**With `--last 7d`**:
```
Readiness Trend (last 7 days)

  Date        Score  Label      HRV  Sleep  Form  Volume
  2026-04-03     72  Easy Day    78     62    80      68
  2026-04-02     65  Easy Day    70     58    72      60
  2026-04-01     45  Rest        40     55    50      35
  ...

  Average: 61  |  Best: 72 (Apr 3)  |  Worst: 45 (Apr 1)
```

### JSON Output (`--json`)

**Today only**:
```json
{
  "date": "2026-04-03",
  "score": 72,
  "label": "Easy Day",
  "recommendation": "Good day for an easy aerobic run or cross-training.",
  "components": {
    "hrv": {"score": 78, "weight": 0.30, "available": true, "description": "HRV 52ms vs 48ms baseline — above average"},
    "sleep": {"score": 62, "weight": 0.20, "available": true, "description": "Sleep score: 62/100"},
    "form": {"score": 80, "weight": 0.30, "available": true, "description": "TSB: +8.2 — fresh"},
    "volume": {"score": 68, "weight": 0.20, "available": true, "description": "7d volume stable vs prior 7d"}
  }
}
```

**With `--last 7d`**:
```json
{
  "today": { ... },
  "daily": [
    {"date": "2026-04-03", "score": 72, "label": "Easy Day", "components": { ... }},
    {"date": "2026-04-02", "score": 65, "label": "Easy Day", "components": { ... }}
  ],
  "summary": {"average": 61, "best": {"date": "2026-04-03", "score": 72}, "worst": {"date": "2026-04-01", "score": 45}}
}
```

### Error Cases

| Condition | Human Output | JSON Output |
|-----------|-------------|-------------|
| No data at all | "No training or health data found. Run 'openactivity strava sync' or 'openactivity garmin import' first." | `{"error": "no_data", "message": "..."}` |
| Training data only (no Garmin) | Partial score with note: "HRV and sleep data unavailable — score based on training data only" | Components with `"available": false` |
