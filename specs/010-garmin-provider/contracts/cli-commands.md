# CLI Command Contracts: Garmin Provider

**Feature**: 010-garmin-provider
**Date**: 2026-03-23
**Purpose**: Define command-line interface structure and behavior

## Overview

This document specifies all CLI commands for the Garmin provider, including both provider-specific commands and modifications to existing unified commands. All commands follow the project's CLI conventions: provider-first hierarchy, `--json` flag support, stderr for errors, stdout for data.

---

## Provider-Specific Commands

### `openactivity garmin`

**Purpose**: Root command group for all Garmin-specific operations

**Usage**:
```bash
openactivity garmin [SUBCOMMAND]
```

**Subcommands**:
- `auth` - Authenticate with Garmin Connect
- `sync` - Sync activities and health data
- `athlete` - View athlete profile
- `activities` - Manage Garmin activities
- `daily` - View health/wellness data

**Flags**: None (flags are specific to subcommands)

**Exit Codes**:
- `0` - Success
- `1` - Command error
- `2` - Invalid arguments

---

### `openactivity garmin auth`

**Purpose**: Authenticate CLI with Garmin Connect credentials

**Usage**:
```bash
openactivity garmin auth [OPTIONS]
```

**Options**:
```
--status          Show current authentication status (no login attempt)
--json            Output in JSON format
--help            Show help message
```

**Interactive Flow** (default, no flags):
```bash
$ openactivity garmin auth
Garmin Connect Authentication

Username: user@example.com
Password: ************

Authenticating with Garmin Connect...
✓ Authentication successful
Credentials stored securely in system keyring

Note: Two-factor authentication (MFA) is not fully supported.
If you have MFA enabled, you may need to use an app-specific password.
```

**Status Check** (`--status`):
```bash
$ openactivity garmin auth --status
Garmin Connect: Authenticated
Last verified: 2026-03-23 08:00:00
Username: user@example.com
```

**JSON Output** (`--json`):
```json
{
  "status": "success",
  "authenticated": true,
  "username": "user@example.com",
  "last_verified": "2026-03-23T08:00:00Z"
}
```

**Error Cases**:
- Invalid credentials:
  ```
  Error: Authentication failed
  Invalid username or password. Please try again.
  ```

- Already authenticated (re-auth attempt):
  ```
  Warning: Garmin credentials already stored
  Overwrite existing credentials? (y/n):
  ```

**Exit Codes**:
- `0` - Success
- `1` - Authentication failed
- `2` - Invalid arguments

---

### `openactivity garmin sync`

**Purpose**: Sync activities and health data from Garmin Connect

**Usage**:
```bash
openactivity garmin sync [OPTIONS]
```

**Options**:
```
--full            Full sync (ignore last sync time, re-sync all data)
--activities-only Sync only activities (skip health data)
--health-only     Sync only health data (skip activities)
--json            Output in JSON format
--help            Show help message
```

**Default Behavior** (incremental sync):
```bash
$ openactivity garmin sync
Syncing from Garmin Connect...

Syncing activities...
  ✓ Fetched 15 new activities
  ✓ Updated 3 existing activities
  ✓ Linked 12 duplicate activities with Strava

Syncing health data...
  ✓ Synced daily summaries for 7 days
  ✓ Synced 8 sleep sessions

Sync complete
  Duration: 42 seconds
  Activities: 15 new, 3 updated
  Health days: 7
  Duplicates detected: 12
```

**Full Sync** (`--full`):
```bash
$ openactivity garmin sync --full
Warning: Full sync will re-download all data from Garmin Connect
This may take several minutes. Continue? (y/n): y

Syncing from Garmin Connect (full sync)...
[Progress bar or spinner]
...
```

**JSON Output** (`--json`):
```json
{
  "status": "success",
  "duration_seconds": 42,
  "activities": {
    "new": 15,
    "updated": 3,
    "errors": 0
  },
  "health": {
    "daily_summaries": 7,
    "sleep_sessions": 8
  },
  "duplicates_detected": 12,
  "last_sync": "2026-03-23T10:30:00Z"
}
```

**Error Cases**:
- Not authenticated:
  ```
  Error: Not authenticated with Garmin Connect
  Run 'openactivity garmin auth' first.
  ```

- API rate limit:
  ```
  Error: Garmin API rate limit exceeded
  Waiting 120 seconds before retry...
  ```

- Network error:
  ```
  Error: Failed to connect to Garmin Connect
  Check your internet connection and try again.
  ```

**Exit Codes**:
- `0` - Success (even with some errors if overall sync succeeded)
- `1` - Complete failure (no data synced)
- `2` - Invalid arguments

---

### `openactivity garmin athlete`

**Purpose**: View Garmin Connect athlete profile

**Usage**:
```bash
openactivity garmin athlete [OPTIONS]
```

**Options**:
```
--json   Output in JSON format
--help   Show help message
```

**Output** (default):
```bash
$ openactivity garmin athlete
Garmin Connect Profile

Name: John Doe
Email: john@example.com
Age: 34
Gender: Male
Weight: 75.0 kg
Max HR: 186 bpm
Resting HR: 52 bpm

Activity Zones (Heart Rate):
  Zone 1 (Easy):       < 130 bpm
  Zone 2 (Moderate):   130-149 bpm
  Zone 3 (Tempo):      150-167 bpm
  Zone 4 (Threshold):  168-177 bpm
  Zone 5 (Maximum):    178+ bpm
```

**JSON Output** (`--json`):
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "age": 34,
  "gender": "Male",
  "weight_kg": 75.0,
  "max_hr": 186,
  "resting_hr": 52,
  "zones": {
    "hr": [
      {"zone": 1, "name": "Easy", "min": 0, "max": 130},
      {"zone": 2, "name": "Moderate", "min": 130, "max": 149},
      {"zone": 3, "name": "Tempo", "min": 150, "max": 167},
      {"zone": 4, "name": "Threshold", "min": 168, "max": 177},
      {"zone": 5, "name": "Maximum", "min": 178, "max": 999}
    ]
  }
}
```

---

### `openactivity garmin activities list`

**Purpose**: List Garmin activities (provider-specific alternative to unified command)

**Usage**:
```bash
openactivity garmin activities list [OPTIONS]
```

**Options**:
```
--limit <N>    Number of activities to show (default: 20)
--type <TYPE>  Filter by activity type (Run, Ride, etc.)
--json         Output in JSON format
--help         Show help message
```

**Output**: Same format as `openactivity activities list --provider garmin`

---

### `openactivity garmin daily`

**Purpose**: View daily health/wellness metrics from Garmin

**Usage**:
```bash
openactivity garmin daily [OPTIONS]
```

**Options**:
```
--last <PERIOD>  Time period (e.g., 7d, 30d, 90d, 1y) (default: 7d)
--date <DATE>    Specific date (YYYY-MM-DD format)
--json           Output in JSON format
--help           Show help message
```

**Output** (last 7 days):
```bash
$ openactivity garmin daily --last 7d
Health Summary (Last 7 Days)

Date        Rest HR  HRV  Body Battery  Stress  Sleep  Steps
────────────────────────────────────────────────────────────
2026-03-23    52     65    15-95         32      78    12456
2026-03-22    54     62    20-92         28      82    10234
2026-03-21    53     68    25-98         24      85    15678
2026-03-20    55     60    18-88         45      68     8932
2026-03-19    52     67    22-96         30      80    11245
2026-03-18    51     70    28-99         20      88    14532
2026-03-17    53     64    15-90         38      72     9876

Averages:
  Resting HR: 53 bpm
  HRV: 65 ms
  Body Battery Range: 20-94
  Stress: 31
  Sleep Score: 79
  Steps: 11,850/day
```

**Single Date** (`--date`):
```bash
$ openactivity garmin daily --date 2026-03-22
Health Summary for 2026-03-22

Resting Heart Rate: 54 bpm
HRV: 62 ms
Body Battery: 20 (min) - 92 (max)
Stress Average: 28
Sleep Score: 82
Steps: 10,234
Respiration: 14.2 breaths/min
SpO2: 96.5%

Sleep Detail:
  Sleep Start: 2026-03-21 22:30
  Sleep End:   2026-03-22 06:45
  Total: 8h 15m
  Deep: 2h 0m (24%)
  Light: 5h 0m (61%)
  REM: 1h 0m (12%)
  Awake: 15m (3%)
```

**JSON Output** (`--json`):
```json
{
  "date": "2026-03-22",
  "resting_hr": 54,
  "hrv_avg": 62,
  "body_battery": {"min": 20, "max": 92},
  "stress_avg": 28,
  "sleep_score": 82,
  "steps": 10234,
  "respiration_avg": 14.2,
  "spo2_avg": 96.5,
  "sleep_sessions": [
    {
      "start": "2026-03-21T22:30:00Z",
      "end": "2026-03-22T06:45:00Z",
      "total_duration_seconds": 29700,
      "deep_duration_seconds": 7200,
      "light_duration_seconds": 18000,
      "rem_duration_seconds": 3600,
      "awake_duration_seconds": 900,
      "sleep_score": 82
    }
  ]
}
```

---

## Unified Commands (Modified)

### `openactivity activity <ID>`

**Purpose**: View activity details (auto-detects provider)

**Modification**: Auto-detect provider from database instead of assuming Strava

**Usage**:
```bash
openactivity activity <ID> [OPTIONS]
```

**Options**: (unchanged from existing)
```
--json   Output in JSON format
--help   Show help message
```

**Behavior Change**:
- Previous: Only searched Strava activities (assumed `id` was Strava ID)
- New: Searches all providers by `id` OR `provider_id`
- If linked activity, shows provider badge: `[Strava+Garmin]`

**Example Output**:
```bash
$ openactivity activity 12345
Morning Run [Strava+Garmin]  # <-- Badge indicates linked activity

Date: 2026-03-23 06:00:00
Type: Run
Distance: 5.01 km
Time: 24:55 (4:58/km pace)
Elevation: +42m

Primary Source: Strava
Also available from: Garmin

[Rest of output same as before]
```

---

### `openactivity activities list`

**Purpose**: List all activities from all providers

**Modification**: Add provider badges and `--provider` filter

**Usage**:
```bash
openactivity activities list [OPTIONS]
```

**New Options**:
```
--provider <NAME>  Filter by provider (strava|garmin)
```

**Existing Options**: (unchanged)
```
--limit <N>       Number of activities (default: 20)
--type <TYPE>     Filter by activity type
--after <DATE>    Activities after date
--before <DATE>   Activities before date
--sort <FIELD>    Sort by (date|distance|duration)
--json            JSON output
--help            Help message
```

**Output** (with provider badges):
```bash
$ openactivity activities list --limit 10
ID      Date        Type  Name                  Distance  Time     Provider
──────────────────────────────────────────────────────────────────────────────
67890   2026-03-23  Run   Morning Run           5.01 km   24:55    [Strava+Garmin]
67889   2026-03-22  Run   Easy Recovery         8.21 km   42:30    [Garmin]
67888   2026-03-21  Ride  Lunch Ride            32.5 km   1:15:20  [Strava]
...
```

**Filter by Provider**:
```bash
$ openactivity activities list --provider garmin --limit 5
# Shows only Garmin activities (including linked ones where Garmin is primary)
```

**JSON Output** (with provider field):
```json
{
  "activities": [
    {
      "id": 67890,
      "provider": "strava",
      "linked": true,
      "linked_providers": ["strava", "garmin"],
      "primary_provider": "strava",
      "name": "Morning Run",
      "date": "2026-03-23T06:00:00Z",
      "distance": 5010.0,
      "elapsed_time": 1495
    }
  ],
  "total": 1,
  "limit": 20
}
```

---

## Common Patterns

### Error Handling

All commands follow this error format:

**Human-readable** (default):
```
Error: [error_code]
[Detailed message]
[Actionable suggestion]
```

**JSON** (`--json`):
```json
{
  "status": "error",
  "error_code": "authentication_required",
  "message": "Not authenticated with Garmin Connect",
  "suggestion": "Run 'openactivity garmin auth' first"
}
```

### Progress Indicators

Commands that may take >2 seconds show progress:

```bash
Syncing activities... [████████░░░░░░░░░░░░] 45% (90/200)
```

### Help Text

All commands must include `--help` with:
- Brief description
- Usage examples
- Option descriptions
- Related commands

Example:
```bash
$ openactivity garmin sync --help
Sync activities and health data from Garmin Connect

Usage:
  openactivity garmin sync [OPTIONS]

Options:
  --full             Full sync (re-sync all data)
  --activities-only  Skip health data sync
  --health-only      Skip activity sync
  --json             JSON output format
  --help             Show this message

Examples:
  # Incremental sync (default)
  openactivity garmin sync

  # Full re-sync
  openactivity garmin sync --full

  # Sync only health data
  openactivity garmin sync --health-only

Related commands:
  garmin auth        Authenticate with Garmin
  activities list    View all synced activities
```

---

## Backward Compatibility

### Existing Commands (Unchanged)

These commands continue to work exactly as before:

- `openactivity strava auth`
- `openactivity strava sync`
- `openactivity strava athlete`
- `openactivity strava activities list`
- `openactivity strava segments *`
- `openactivity strava analyze *`
- `openactivity strava predict *`
- All other Strava-specific commands

### Migration Notes

- No breaking changes to existing commands
- Users with only Strava will see no difference
- `activity <ID>` and `activities list` enhancements are additive (new features, not changes)
- Provider badges only appear when multiple providers are configured

---

## Command Reference Summary

| Command | Purpose | Output Type |
|---------|---------|-------------|
| `garmin auth` | Authenticate | Interactive / Status |
| `garmin auth --status` | Check auth status | Status display |
| `garmin sync` | Sync all data | Progress + Summary |
| `garmin sync --full` | Full re-sync | Progress + Summary |
| `garmin athlete` | Profile info | Profile display |
| `garmin activities list` | List activities | Table / JSON |
| `garmin daily` | Health metrics | Table / JSON |
| `garmin daily --date <date>` | Single day detail | Detailed display |
| `activity <ID>` | Activity detail (any provider) | Activity display |
| `activities list` | All activities (all providers) | Table / JSON |
| `activities list --provider <name>` | Filter by provider | Table / JSON |

**Total New Commands**: 6 (all under `garmin` group)
**Modified Commands**: 2 (`activity`, `activities list`)
**Unchanged Commands**: All existing Strava commands (20+)
