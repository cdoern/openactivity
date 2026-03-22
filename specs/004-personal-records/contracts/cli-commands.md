# CLI Command Contract: Personal Records Database

**Branch**: `004-personal-records` | **Date**: 2026-03-21

## Command Group: `openactivity strava records`

### `openactivity strava records scan`

**Description**: Scan synced activities to detect personal records.

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--full` | bool | No | False | Re-scan all activities (reset scan state) |

```bash
openactivity strava records scan
openactivity strava records scan --full
openactivity strava records scan --json
```

**Output (table)**: Progress bar during scan, then summary of new/updated PRs found.
**Output (JSON)**: `{"scanned": 42, "new_records": 3, "updated_records": 1, "records": [...]}`

---

### `openactivity strava records list`

**Description**: Show current personal records.

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--type` | string | No | None (all) | Filter by "running" or "cycling" |

```bash
openactivity strava records list
openactivity strava records list --type running
openactivity strava records list --json
```

**Table Output**:
```
              Personal Records — Running
┏━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Distance    ┃ Time      ┃ Pace      ┃ Date       ┃ Activity             ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ 1 mile      │ 6:12      │ 3:51 /km  │ 2026-02-14 │ Morning Tempo Run    │
│ 5K          │ 21:45     │ 4:21 /km  │ 2026-01-20 │ Parkrun #52          │
│ 10K         │ 46:30     │ 4:39 /km  │ 2025-11-05 │ Turkey Trot 10K      │
│ Half        │ 1:42:15   │ 4:51 /km  │ 2025-10-12 │ Fall Half Marathon   │
│ Marathon    │ 3:45:00   │ 5:20 /km  │ 2025-04-21 │ Boston Marathon       │
│ 15K *       │ 1:10:30   │ 4:42 /km  │ 2025-09-01 │ Falmouth Road Race   │
└─────────────┴───────────┴───────────┴────────────┴──────────────────────┘
  * = custom distance

              Personal Records — Cycling Power
┏━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Duration    ┃ Power     ┃ Date       ┃ Activity             ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ 5 seconds   │ 1,150 W   │ 2026-03-01 │ Sprint Intervals     │
│ 1 minute    │ 420 W     │ 2026-02-20 │ Hill Repeats         │
│ 5 minutes   │ 310 W     │ 2026-01-15 │ Tempo Ride           │
│ 20 minutes  │ 275 W     │ 2025-12-10 │ FTP Test             │
│ 60 minutes  │ 255 W     │ 2025-11-22 │ Century Ride         │
└─────────────┴───────────┴────────────┴──────────────────────┘
```

---

### `openactivity strava records history --distance <DISTANCE>`

**Description**: Show PR progression for a specific distance or power duration.

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--distance` | string | Yes | — | Distance label (e.g., "5K", "1mi", "20min") |

```bash
openactivity strava records history --distance 5K
openactivity strava records history --distance 20min --json
```

**Table Output**:
```
              5K PR Progression
┏━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ #   ┃ Date       ┃ Time      ┃ Pace      ┃ Improvement  ┃ Activity             ┃
┡━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ 1   │ 2024-03-10 │ 28:15     │ 5:39 /km  │ —            │ First 5K Attempt     │
│ 2   │ 2024-09-22 │ 25:30     │ 5:06 /km  │ -2:45        │ Fall Race Series     │
│ 3   │ 2025-06-14 │ 23:00     │ 4:36 /km  │ -2:30        │ Summer 5K PR         │
│ 4 ★ │ 2026-01-20 │ 21:45     │ 4:21 /km  │ -1:15        │ Parkrun #52          │
└─────┴────────────┴───────────┴───────────┴──────────────┴──────────────────────┘
  ★ = current PR
```

---

### `openactivity strava records add-distance <LABEL> <METERS>`

**Description**: Add a custom distance for PR tracking.

```bash
openactivity strava records add-distance 15K 15000
openactivity strava records add-distance 50K 50000
```

**Output**: `Added custom distance: 15K (15,000 m). Run 'openactivity strava records scan' to detect PRs.`

---

### `openactivity strava records remove-distance <LABEL>`

**Description**: Remove a custom distance and its records.

```bash
openactivity strava records remove-distance 15K
```

**Output**: `Removed custom distance '15K' and 3 associated records.`
**Error**: `Cannot remove standard distance '5K'. Only custom distances can be removed.`

---

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid input (unknown distance label, invalid meters) |
| 2 | No synced data available |
