# CLI Command Contract: OpenActivity Strava

**Date**: 2026-03-13

## Global Flags

All commands support:

| Flag             | Type   | Default  | Description                           |
|------------------|--------|----------|---------------------------------------|
| `--json`         | bool   | false    | Output as JSON to stdout              |
| `--units`        | string | "metric" | Unit system: "metric" or "imperial"   |
| `--config`       | string | ""       | Path to config file override          |
| `--help`         | bool   | false    | Show help text with usage examples    |

## Command Tree

```
openactivity
├── strava
│   ├── auth              # OAuth setup and management
│   │   └── revoke        # Remove stored credentials
│   ├── sync              # Sync data from Strava API
│   ├── athlete           # View authenticated user profile
│   ├── activities
│   │   ├── list          # List activities from local store
│   │   └── export        # Bulk export activities
│   ├── activity <ID>     # View single activity detail
│   ├── analyze
│   │   ├── summary       # Training volume summaries
│   │   ├── pace          # Pace trend analysis
│   │   ├── zones         # HR/power zone distributions
│   │   └── power-curve   # Best power for durations
│   └── segments
│       ├── list          # List starred segments
│       ├── segment <ID>
│       │   ├── efforts   # View segment efforts
│       │   └── leaderboard # View leaderboard
```

## Command Specifications

### `openactivity strava auth`

**Purpose**: Configure Strava API credentials and complete OAuth authorization.

**First run flow**:
1. Prompt for client ID and client secret
2. Store credentials in OS keychain
3. Open browser for OAuth authorization
4. Listen on localhost for callback
5. Exchange code for access + refresh tokens
6. Store tokens in OS keychain

**Subsequent runs**: Re-authorize (refresh OAuth tokens).

**Output (human)**:
```
✓ Authenticated as Charlie Doern (@cdoern)
  Token expires: 2026-03-13T18:00:00Z
```

**Output (JSON)**:
```json
{
  "athlete_id": 12345,
  "username": "cdoern",
  "name": "Charlie Doern",
  "token_expires_at": "2026-03-13T18:00:00Z",
  "scopes": ["activity:read_all", "profile:read_all"]
}
```

---

### `openactivity strava auth revoke`

**Purpose**: Remove all stored credentials and tokens.

**Output**: Confirmation message.

---

### `openactivity strava sync`

**Purpose**: Fetch data from Strava API into local storage.

| Flag       | Type   | Default | Description                              |
|------------|--------|---------|------------------------------------------|
| `--full`   | bool   | false   | Re-sync all data (ignore last sync time) |
| `--detail` | bool   | true    | Fetch detailed data (streams, laps, zones) |

**Behavior**:
- Incremental by default (only new/updated since last sync)
- Fetches: activities, athlete profile, athlete stats, gear, segments
- With `--detail`: also fetches streams, laps, zones per activity
- Displays progress bar during sync
- Handles rate limits with automatic pause/resume
- Resumable if interrupted (tracks sync state)

**Output (human)**:
```
Syncing activities...
  ████████████████████░░░░ 42/50 activities
  ⏳ Rate limit: pausing 12m (resets 14:30)
  ████████████████████████ 50/50 activities
✓ Synced 50 activities (12 new, 38 updated)
  Last sync: 2026-03-13T14:22:00Z
```

**Output (JSON)**:
```json
{
  "synced": 50,
  "new": 12,
  "updated": 38,
  "errors": 0,
  "last_sync": "2026-03-13T14:22:00Z",
  "duration_seconds": 45
}
```

---

### `openactivity strava athlete`

**Purpose**: Display authenticated user's profile and stats.

**Output (human)**:
```
Charlie Doern (@cdoern)
  Location: Washington, DC, US

  Year-to-Date          All-Time
  ──────────────        ──────────────
  Runs: 45              Runs: 892
  Distance: 312.5 km    Distance: 8,431.2 km
  Time: 28h 15m         Time: 742h 30m
  Elevation: 2,100 m    Elevation: 52,300 m
```

---

### `openactivity strava activities list`

**Purpose**: List activities from local storage.

| Flag       | Type   | Default | Description                           |
|------------|--------|---------|---------------------------------------|
| `--type`   | string | ""      | Filter by activity type (run, ride)   |
| `--after`  | string | ""      | Filter: activities after date (ISO)   |
| `--before` | string | ""      | Filter: activities before date (ISO)  |
| `--search` | string | ""      | Search by activity name               |
| `--limit`  | int    | 20      | Max results to display                |
| `--offset` | int    | 0       | Skip first N results                  |
| `--sort`   | string | "date"  | Sort by: date, distance, duration     |

**Output (human)**:
```
 ID          Date        Type   Name                    Distance    Time      Elev
 ──────────  ──────────  ────   ──────────────────────  ──────────  ────────  ─────
 12345678    2026-03-12  Run    Morning 10K             10.2 km     48:32     85 m
 12345677    2026-03-10  Ride   Evening Ride            42.1 km     1:32:10   320 m
 12345676    2026-03-09  Run    Tempo Run               8.0 km      36:15     45 m

Showing 3 of 892 activities. Use --limit and --offset for pagination.
```

**Output (JSON)**: Array of activity objects.

---

### `openactivity strava activity <ID>`

**Purpose**: Show detailed information for a single activity.

| Flag         | Type   | Default | Description                        |
|--------------|--------|---------|------------------------------------|
| `--export`   | string | ""      | Export format: "gpx", "csv"        |
| `--output`   | string | ""      | Output file path (for export)      |

**Output (human)**: Formatted detail view with sections for summary, splits/laps, zone distributions, and gear.

---

### `openactivity strava activities export`

**Purpose**: Bulk export activities.

| Flag         | Type   | Default | Description                        |
|--------------|--------|---------|------------------------------------|
| `--format`   | string | "csv"   | Export format: "csv", "json"       |
| `--output`   | string | ""      | Output file path                   |
| `--after`    | string | ""      | Filter: after date                 |
| `--before`   | string | ""      | Filter: before date                |
| `--type`     | string | ""      | Filter: activity type              |
| `--force`    | bool   | false   | Overwrite existing file            |

---

### `openactivity strava analyze summary`

**Purpose**: Training volume summary over time.

| Flag       | Type   | Default  | Description                          |
|------------|--------|----------|--------------------------------------|
| `--period` | string | "weekly" | Aggregation: "daily", "weekly", "monthly" |
| `--last`   | string | "90d"   | Time window (e.g., "30d", "6m", "1y") |
| `--type`   | string | ""       | Filter by activity type              |
| `--chart`  | string | ""       | Chart type: "bar", "line"            |
| `--output` | string | ""       | Chart output file path               |

---

### `openactivity strava analyze pace`

**Purpose**: Pace trend analysis over time.

| Flag       | Type   | Default | Description                          |
|------------|--------|---------|--------------------------------------|
| `--last`   | string | "90d"   | Time window                          |
| `--type`   | string | "run"   | Activity type (run, ride, swim)      |
| `--chart`  | string | ""      | Chart type: "line", "scatter"        |
| `--output` | string | ""      | Chart output file path               |

---

### `openactivity strava analyze zones`

**Purpose**: Heart rate or power zone distribution.

| Flag         | Type   | Default     | Description                      |
|--------------|--------|-------------|----------------------------------|
| `--zone-type`| string | "heartrate" | "heartrate" or "power"           |
| `--type`     | string | ""          | Filter by activity type          |
| `--last`     | string | "all"       | Time window                      |
| `--chart`    | string | ""          | Chart type: "bar", "pie"         |
| `--output`   | string | ""          | Chart output file path           |

---

### `openactivity strava analyze power-curve`

**Purpose**: Best average power for key durations.

| Flag       | Type   | Default | Description                          |
|------------|--------|---------|--------------------------------------|
| `--last`   | string | "90d"   | Time window                          |
| `--chart`  | string | ""      | Chart type: "line"                   |
| `--output` | string | ""      | Chart output file path               |

**Output (human)**:
```
Power Curve (last 90 days)

  Duration    Best Power    Date
  ──────────  ──────────    ──────────
  5s          950 W         2026-02-15
  1min        420 W         2026-02-15
  5min        310 W         2026-01-22
  20min       265 W         2026-03-01
  60min       240 W         2026-02-28
```

---

### `openactivity strava segments list`

**Purpose**: List starred segments.

| Flag       | Type   | Default | Description                       |
|------------|--------|---------|-----------------------------------|
| `--type`   | string | ""      | Filter: "ride" or "run"          |
| `--limit`  | int    | 20      | Max results                       |

---

### `openactivity strava segment <ID> efforts`

**Purpose**: View all efforts on a segment.

| Flag       | Type   | Default | Description                       |
|------------|--------|---------|-----------------------------------|
| `--limit`  | int    | 20      | Max results                       |

---

### `openactivity strava segment <ID> leaderboard`

**Purpose**: View segment leaderboard.

| Flag           | Type   | Default | Description                   |
|----------------|--------|---------|-------------------------------|
| `--gender`     | string | ""      | Filter: "M" or "F"           |
| `--age-group`  | string | ""      | Filter: e.g., "25_34"        |
| `--friends`    | bool   | false   | Show only friends             |
| `--limit`      | int    | 10      | Max results                   |

## Error Output Contract

All errors written to stderr in format:
```
Error: <what went wrong>
  <why it happened>
  <what to do about it>
```

Example:
```
Error: Authentication required
  No stored credentials found for Strava.
  Run 'openactivity strava auth' to connect your account.
```

With `--json`, errors emit:
```json
{
  "error": "authentication_required",
  "message": "No stored credentials found for Strava.",
  "hint": "Run 'openactivity strava auth' to connect your account."
}
```
