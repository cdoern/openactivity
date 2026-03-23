# Data Model: Garmin Connect Provider

**Feature**: 010-garmin-provider
**Date**: 2026-03-23
**Purpose**: Define database schema and data entities

## Overview

This feature extends the existing data model to support multiple activity providers (Strava + Garmin) and adds Garmin-specific health/wellness data. The design prioritizes backward compatibility while enabling provider-agnostic queries and activity deduplication.

---

## Modified Entities

### Activity (Extended)

**Purpose**: Existing activity entity extended with multi-provider support

**New Fields**:
- `provider`: String enum ("strava" | "garmin") - identifies data source
- `provider_id`: Integer - original activity ID from provider's API

**Existing Fields** (unchanged):
- `id`: Integer (primary key, auto-increment)
- `athlete_id`: Integer
- `name`: String
- `type`: String
- `start_date`: DateTime
- `distance`: Float
- `moving_time`: Integer
- `elapsed_time`: Integer
- `total_elevation_gain`: Float
- `average_heartrate`: Float (nullable)
- ... (all other existing fields)

**Indexes**:
- Primary: `id`
- New: `(provider, provider_id)` - for provider-specific lookups
- Existing: `(athlete_id, start_date)` - chronological queries

**Validation Rules**:
- `provider` must be one of: "strava", "garmin"
- `provider_id` must not be null (required for all new records)
- For backward compatibility: existing records default to provider="strava", provider_id=id

**Example Records**:
```json
// Strava activity (migrated)
{
  "id": 12345,
  "provider": "strava",
  "provider_id": 12345,
  "name": "Morning Run",
  "start_date": "2026-03-23T06:00:00Z",
  "distance": 5000.0,
  "elapsed_time": 1500
}

// Garmin activity
{
  "id": 67890,
  "provider": "garmin",
  "provider_id": 98765432,  // Garmin's internal ID
  "name": "Morning Run",
  "start_date": "2026-03-23T06:00:15Z",  // 15 seconds later (clock diff)
  "distance": 5010.0,  // Slightly different GPS measurement
  "elapsed_time": 1495
}
```

**State Transitions**: None (activities are immutable once synced)

---

## New Entities

### ActivityLink

**Purpose**: Links duplicate activities from different providers

**Fields**:
- `id`: Integer (primary key)
- `strava_activity_id`: Integer (foreign key to activities.id, nullable)
- `garmin_activity_id`: Integer (foreign key to activities.id, nullable)
- `primary_provider`: String enum ("strava" | "garmin") - which provider is authoritative
- `match_confidence`: Float (0.0-1.0) - confidence score of the match
- `created_at`: DateTime (auto-populated)

**Relationships**:
- One-to-one with Activity (Strava side)
- One-to-one with Activity (Garmin side)
- At least one of strava_activity_id or garmin_activity_id must be non-null

**Indexes**:
- Primary: `id`
- Unique: `strava_activity_id` (if not null)
- Unique: `garmin_activity_id` (if not null)

**Validation Rules**:
- At least one activity ID must be present
- Both activity IDs must exist in activities table
- Both activities must have different providers
- `match_confidence` must be between 0.0 and 1.0
- `primary_provider` must match one of the linked activities' providers

**Example Record**:
```json
{
  "id": 1,
  "strava_activity_id": 12345,
  "garmin_activity_id": 67890,
  "primary_provider": "strava",  // Strava had more data (HR, power)
  "match_confidence": 0.95,      // High confidence match
  "created_at": "2026-03-23T10:00:00Z"
}
```

---

### GarminDailySummary

**Purpose**: Daily health/wellness metrics from Garmin Connect

**Fields**:
- `id`: Integer (primary key)
- `date`: Date (unique) - the calendar date for this summary
- `resting_hr`: Integer (nullable) - resting heart rate in BPM
- `hrv_avg`: Integer (nullable) - average HRV in milliseconds
- `body_battery_max`: Integer (nullable) - max Body Battery level (0-100)
- `body_battery_min`: Integer (nullable) - min Body Battery level (0-100)
- `stress_avg`: Integer (nullable) - average stress score (0-100)
- `sleep_score`: Integer (nullable) - overall sleep quality score (0-100)
- `steps`: Integer (nullable) - total step count
- `respiration_avg`: Float (nullable) - average respiration rate (breaths/min)
- `spo2_avg`: Float (nullable) - average SpO2 percentage
- `synced_at`: DateTime (auto-populated)

**Indexes**:
- Primary: `id`
- Unique: `date`

**Validation Rules**:
- `date` must be unique (one summary per day)
- Numeric values must be within valid ranges:
  - `resting_hr`: 30-200 BPM
  - `hrv_avg`: 0-300 ms
  - `body_battery_max/min`: 0-100
  - `stress_avg`: 0-100
  - `sleep_score`: 0-100
  - `spo2_avg`: 70-100%
- All nullable fields may be null (not all users have all sensors)

**Example Record**:
```json
{
  "id": 42,
  "date": "2026-03-22",
  "resting_hr": 52,
  "hrv_avg": 65,
  "body_battery_max": 95,
  "body_battery_min": 15,
  "stress_avg": 32,
  "sleep_score": 78,
  "steps": 12456,
  "respiration_avg": 14.2,
  "spo2_avg": 96.5,
  "synced_at": "2026-03-23T08:00:00Z"
}
```

**State Transitions**:
- Created when first synced for a date
- Updated if re-synced (Garmin may update historical data)
- Never deleted (historical record)

---

### GarminSleepSession

**Purpose**: Detailed sleep tracking data from Garmin devices

**Fields**:
- `id`: Integer (primary key)
- `date`: Date - the date this sleep session ended (for grouping)
- `start_time`: DateTime - when sleep started
- `end_time`: DateTime - when sleep ended
- `total_duration_seconds`: Integer - total time in bed
- `deep_duration_seconds`: Integer (nullable) - time in deep sleep
- `light_duration_seconds`: Integer (nullable) - time in light sleep
- `rem_duration_seconds`: Integer (nullable) - time in REM sleep
- `awake_duration_seconds`: Integer (nullable) - time awake in bed
- `sleep_score`: Integer (nullable) - quality score (0-100)
- `synced_at`: DateTime (auto-populated)

**Indexes**:
- Primary: `id`
- Index: `date` (for queries like "show sleep for past week")
- Index: `start_time` (for chronological ordering)

**Validation Rules**:
- `start_time` < `end_time`
- `total_duration_seconds` >= sum of all phase durations
- Phase durations must be non-negative
- `sleep_score` must be 0-100 if present
- `date` should match the calendar date of `end_time` (sleep session attributed to the day it ended)

**Relationships**:
- One-to-many with date (multiple sleep sessions per day: nighttime sleep + naps)

**Example Records**:
```json
// Nighttime sleep
{
  "id": 100,
  "date": "2026-03-23",
  "start_time": "2026-03-22T22:30:00Z",
  "end_time": "2026-03-23T06:45:00Z",
  "total_duration_seconds": 29700,  // ~8.25 hours
  "deep_duration_seconds": 7200,    // 2 hours deep
  "light_duration_seconds": 18000,  // 5 hours light
  "rem_duration_seconds": 3600,     // 1 hour REM
  "awake_duration_seconds": 900,    // 15 min awake
  "sleep_score": 82,
  "synced_at": "2026-03-23T08:00:00Z"
}

// Afternoon nap
{
  "id": 101,
  "date": "2026-03-23",
  "start_time": "2026-03-23T14:00:00Z",
  "end_time": "2026-03-23T14:45:00Z",
  "total_duration_seconds": 2700,   // 45 min
  "deep_duration_seconds": null,    // Naps may not have phase detail
  "light_duration_seconds": null,
  "rem_duration_seconds": null,
  "awake_duration_seconds": null,
  "sleep_score": null,
  "synced_at": "2026-03-23T16:00:00Z"
}
```

**State Transitions**:
- Created when sleep session first detected
- Updated if Garmin refines sleep phase detection (can happen hours later)
- Never deleted

---

## Entity Relationships

```text
Activity 1───────┐
                 │
                 ├──> ActivityLink (optional, for duplicates)
                 │
Activity 2───────┘

Activity.start_date ─────> GarminDailySummary.date (date part, for health context)

GarminDailySummary.date <──── GarminSleepSession.date (one-to-many)
```

**Key Relationships**:
1. **Activity ↔ ActivityLink**: Optional 1:1 relationship. Most activities won't be linked (single-provider only). Linked activities share a common ActivityLink record.

2. **Activity → GarminDailySummary**: Implicit relationship through date matching. Used for queries like "Show me activities with low Body Battery."

3. **GarminDailySummary ↔ GarminSleepSession**: 1:N relationship through date field. A daily summary may reference multiple sleep sessions (night sleep + naps).

---

## Migration Strategy

### Phase 1: Extend Activity Table

```sql
-- Add provider columns with defaults for backward compatibility
ALTER TABLE activities ADD COLUMN provider VARCHAR(20) DEFAULT 'strava';
ALTER TABLE activities ADD COLUMN provider_id INTEGER;

-- Populate provider_id for existing records
UPDATE activities SET provider_id = id WHERE provider = 'strava';

-- Create index for provider lookups
CREATE INDEX idx_activities_provider ON activities(provider, provider_id);
```

### Phase 2: Create New Tables

```sql
-- Activity link table
CREATE TABLE activity_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strava_activity_id INTEGER REFERENCES activities(id) ON DELETE CASCADE,
    garmin_activity_id INTEGER REFERENCES activities(id) ON DELETE CASCADE,
    primary_provider VARCHAR(20) NOT NULL,
    match_confidence REAL CHECK(match_confidence BETWEEN 0.0 AND 1.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (strava_activity_id IS NOT NULL OR garmin_activity_id IS NOT NULL)
);

CREATE UNIQUE INDEX idx_activity_links_strava ON activity_links(strava_activity_id)
    WHERE strava_activity_id IS NOT NULL;
CREATE UNIQUE INDEX idx_activity_links_garmin ON activity_links(garmin_activity_id)
    WHERE garmin_activity_id IS NOT NULL;

-- Garmin health tables
CREATE TABLE garmin_daily_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    resting_hr INTEGER CHECK(resting_hr BETWEEN 30 AND 200),
    hrv_avg INTEGER CHECK(hrv_avg BETWEEN 0 AND 300),
    body_battery_max INTEGER CHECK(body_battery_max BETWEEN 0 AND 100),
    body_battery_min INTEGER CHECK(body_battery_min BETWEEN 0 AND 100),
    stress_avg INTEGER CHECK(stress_avg BETWEEN 0 AND 100),
    sleep_score INTEGER CHECK(sleep_score BETWEEN 0 AND 100),
    steps INTEGER CHECK(steps >= 0),
    respiration_avg REAL CHECK(respiration_avg BETWEEN 0 AND 60),
    spo2_avg REAL CHECK(spo2_avg BETWEEN 70 AND 100),
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE garmin_sleep_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    total_duration_seconds INTEGER NOT NULL CHECK(total_duration_seconds > 0),
    deep_duration_seconds INTEGER CHECK(deep_duration_seconds >= 0),
    light_duration_seconds INTEGER CHECK(light_duration_seconds >= 0),
    rem_duration_seconds INTEGER CHECK(rem_duration_seconds >= 0),
    awake_duration_seconds INTEGER CHECK(awake_duration_seconds >= 0),
    sleep_score INTEGER CHECK(sleep_score BETWEEN 0 AND 100),
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (start_time < end_time)
);

CREATE INDEX idx_sleep_date ON garmin_sleep_session(date);
CREATE INDEX idx_sleep_start ON garmin_sleep_session(start_time);
```

### Rollback Plan

```sql
-- Remove new tables
DROP TABLE IF EXISTS garmin_sleep_session;
DROP TABLE IF EXISTS garmin_daily_summary;
DROP TABLE IF EXISTS activity_links;

-- Remove new columns (SQLite limitation: requires table recreation)
-- Not recommended for production - instead leave columns in place with defaults
```

---

## Query Patterns

### Get All Activities (Provider-Agnostic)

```sql
SELECT
    a.id,
    a.provider,
    a.name,
    a.start_date,
    a.distance,
    CASE
        WHEN al.id IS NOT NULL THEN 'linked'
        ELSE 'single'
    END as link_status
FROM activities a
LEFT JOIN activity_links al ON (
    a.id = al.strava_activity_id OR
    a.id = al.garmin_activity_id
)
ORDER BY a.start_date DESC
LIMIT 20;
```

### Get Activities with Health Context

```sql
SELECT
    a.name,
    a.start_date,
    a.distance,
    gds.body_battery_min,
    gds.resting_hr,
    gds.sleep_score
FROM activities a
LEFT JOIN garmin_daily_summary gds ON DATE(a.start_date) = gds.date
WHERE a.start_date >= '2026-03-01'
ORDER BY a.start_date;
```

### Find Potential Duplicate Activities

```sql
SELECT
    a1.id as strava_id,
    a2.id as garmin_id,
    a1.name,
    a1.start_date as strava_start,
    a2.start_date as garmin_start,
    ABS(JULIANDAY(a1.start_date) - JULIANDAY(a2.start_date)) * 86400 as time_diff_seconds
FROM activities a1
JOIN activities a2 ON
    a1.provider = 'strava' AND
    a2.provider = 'garmin' AND
    ABS(JULIANDAY(a1.start_date) - JULIANDAY(a2.start_date)) * 86400 < 60 AND
    ABS(a1.elapsed_time - a2.elapsed_time) / CAST(a1.elapsed_time AS REAL) < 0.05
WHERE NOT EXISTS (
    SELECT 1 FROM activity_links al
    WHERE al.strava_activity_id = a1.id
       OR al.garmin_activity_id = a2.id
);
```

### Get Sleep Summary for Date Range

```sql
SELECT
    date,
    COUNT(*) as session_count,
    SUM(total_duration_seconds) / 3600.0 as total_hours,
    AVG(sleep_score) as avg_score
FROM garmin_sleep_session
WHERE date BETWEEN '2026-03-01' AND '2026-03-31'
GROUP BY date
ORDER BY date;
```

---

## Data Volume Estimates

**Assumptions**: Active user with both Strava and Garmin

| Entity | Records per Year | Storage per Record | Annual Storage |
|--------|-----------------|-------------------|----------------|
| Activity | ~400 (Strava) + 400 (Garmin) = 800 | ~500 bytes | ~400 KB |
| ActivityLink | ~350 (87.5% match rate) | ~50 bytes | ~17.5 KB |
| GarminDailySummary | 365 | ~100 bytes | ~36.5 KB |
| GarminSleepSession | ~400 (365 nights + 35 naps) | ~80 bytes | ~32 KB |

**Total**: ~486 KB per user per year (negligible - SQLite handles millions of records easily)

**10-Year Projection**: ~4.86 MB per user (well within SQLite limits and performance targets)
