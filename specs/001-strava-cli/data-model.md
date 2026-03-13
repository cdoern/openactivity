# Data Model: OpenActivity Strava CLI

**Date**: 2026-03-13
**Feature**: 001-strava-cli

## Entities

### Athlete

Represents the authenticated Strava user. One per configuration.

| Field              | Type     | Notes                                    |
|--------------------|----------|------------------------------------------|
| id                 | int64    | Strava athlete ID (unique, primary key)  |
| username           | string   | Strava username                          |
| firstname          | string   | First name                               |
| lastname           | string   | Last name                                |
| city               | string   | City from profile                        |
| state              | string   | State/region from profile                |
| country            | string   | Country from profile                     |
| measurement_pref   | string   | "feet" or "meters" (from Strava profile) |
| weight             | float64  | Weight in kg                             |
| ftp                | int      | Functional Threshold Power (cycling)     |
| created_at         | datetime | When record was created locally          |
| updated_at         | datetime | When record was last synced              |

### AthleteStats

Cumulative stats for the athlete (year-to-date and all-time).

| Field                  | Type     | Notes                              |
|------------------------|----------|------------------------------------|
| athlete_id             | int64    | FK to Athlete                      |
| stat_type              | string   | "ytd" or "all_time"                |
| activity_type          | string   | "run", "ride", "swim", etc.        |
| count                  | int      | Number of activities                |
| distance               | float64  | Total distance in meters           |
| moving_time            | int      | Total moving time in seconds       |
| elapsed_time           | int      | Total elapsed time in seconds      |
| elevation_gain         | float64  | Total elevation gain in meters     |
| updated_at             | datetime | Last sync timestamp                |

### Activity

A single workout recorded on Strava.

| Field                  | Type     | Notes                                     |
|------------------------|----------|-------------------------------------------|
| id                     | int64    | Strava activity ID (unique, primary key)  |
| athlete_id             | int64    | FK to Athlete                             |
| name                   | string   | Activity name                             |
| type                   | string   | Activity type (Run, Ride, Swim, etc.)     |
| sport_type             | string   | Sport type (more specific than type)      |
| start_date             | datetime | Activity start time (UTC)                 |
| start_date_local       | datetime | Activity start time (local timezone)      |
| timezone               | string   | Timezone string                           |
| distance               | float64  | Distance in meters                        |
| moving_time            | int      | Moving time in seconds                    |
| elapsed_time           | int      | Elapsed time in seconds                   |
| total_elevation_gain   | float64  | Elevation gain in meters                  |
| average_speed          | float64  | Average speed in m/s                      |
| max_speed              | float64  | Max speed in m/s                          |
| average_heartrate      | float64  | Average heart rate (nullable)             |
| max_heartrate          | float64  | Max heart rate (nullable)                 |
| average_cadence        | float64  | Average cadence (nullable)                |
| average_watts          | float64  | Average power in watts (nullable)         |
| weighted_average_watts | float64  | Normalized power (nullable)               |
| max_watts              | int      | Max power in watts (nullable)             |
| kilojoules             | float64  | Total work in kJ (nullable)               |
| calories               | float64  | Calories burned (nullable)                |
| suffer_score           | int      | Relative effort score (nullable)          |
| gear_id                | string   | FK to Gear (nullable)                     |
| description            | string   | Activity description (nullable)           |
| has_heartrate          | bool     | Whether HR data exists                    |
| has_power              | bool     | Whether power data exists                 |
| start_latlng           | string   | Start coordinates as "lat,lng" (nullable) |
| end_latlng             | string   | End coordinates as "lat,lng" (nullable)   |
| synced_detail          | bool     | Whether detailed data has been synced     |
| created_at             | datetime | When record was created locally           |
| updated_at             | datetime | When record was last synced               |

### Lap

A lap within an activity (auto or manual split).

| Field                | Type     | Notes                                  |
|----------------------|----------|----------------------------------------|
| id                   | int64    | Strava lap ID (unique, primary key)    |
| activity_id          | int64    | FK to Activity                         |
| lap_index            | int      | Lap number (1-based)                   |
| name                 | string   | Lap name (e.g., "Lap 1")              |
| distance             | float64  | Lap distance in meters                 |
| moving_time          | int      | Moving time in seconds                 |
| elapsed_time         | int      | Elapsed time in seconds                |
| total_elevation_gain | float64  | Elevation gain in meters               |
| average_speed        | float64  | Average speed in m/s                   |
| max_speed            | float64  | Max speed in m/s                       |
| average_heartrate    | float64  | Average HR (nullable)                  |
| max_heartrate        | float64  | Max HR (nullable)                      |
| average_cadence      | float64  | Average cadence (nullable)             |
| average_watts        | float64  | Average power (nullable)               |
| start_index          | int      | Stream index where lap starts          |
| end_index            | int      | Stream index where lap ends            |

### ActivityZone

Heart rate or power zone distribution for an activity.

| Field          | Type     | Notes                                    |
|----------------|----------|------------------------------------------|
| id             | int64    | Auto-generated primary key               |
| activity_id    | int64    | FK to Activity                           |
| zone_type      | string   | "heartrate" or "power"                   |
| zone_index     | int      | Zone number (1-based, e.g., Z1-Z5)      |
| min_value      | int      | Zone lower bound (bpm or watts)          |
| max_value      | int      | Zone upper bound (bpm or watts, -1=max)  |
| time_seconds   | int      | Time spent in zone in seconds            |

### AthleteZone

The athlete's configured training zones.

| Field       | Type     | Notes                                     |
|-------------|----------|-------------------------------------------|
| id          | int64    | Auto-generated primary key                |
| athlete_id  | int64    | FK to Athlete                             |
| zone_type   | string   | "heartrate" or "power"                    |
| zone_index  | int      | Zone number (1-based)                     |
| min_value   | int      | Zone lower bound                          |
| max_value   | int      | Zone upper bound (-1 = no upper limit)    |
| updated_at  | datetime | Last sync timestamp                       |

### ActivityStream

Time-series data for an activity (stored as compressed blobs).

| Field        | Type     | Notes                                          |
|--------------|----------|------------------------------------------------|
| id           | int64    | Auto-generated primary key                     |
| activity_id  | int64    | FK to Activity                                 |
| stream_type  | string   | "latlng", "heartrate", "watts", "cadence",     |
|              |          | "altitude", "velocity_smooth", "distance",     |
|              |          | "time", "grade_smooth", "temp", "moving"       |
| data         | blob     | JSON-encoded array of values                   |
| resolution   | string   | "high" (every second) or "low" (sampled)       |

**Note**: Streams are stored as JSON blobs rather than individual rows per data point. A 1-hour activity at 1Hz produces ~3,600 data points per stream type. Storing as blobs keeps the database compact and queries fast.

### Gear

Equipment used for activities (shoes, bikes, etc.).

| Field      | Type     | Notes                                  |
|------------|----------|----------------------------------------|
| id         | string   | Strava gear ID (unique, primary key)   |
| name       | string   | Gear name                              |
| distance   | float64  | Total distance in meters               |
| brand_name | string   | Brand (nullable)                       |
| model_name | string   | Model (nullable)                       |
| gear_type  | string   | "bike" or "shoes"                      |

### Segment

A defined section of road or trail.

| Field                | Type     | Notes                                  |
|----------------------|----------|----------------------------------------|
| id                   | int64    | Strava segment ID (primary key)        |
| name                 | string   | Segment name                           |
| activity_type        | string   | "Ride" or "Run"                        |
| distance             | float64  | Segment distance in meters             |
| average_grade        | float64  | Average grade in percent               |
| maximum_grade        | float64  | Maximum grade in percent               |
| elevation_high       | float64  | Highest elevation in meters            |
| elevation_low        | float64  | Lowest elevation in meters             |
| total_elevation_gain | float64  | Total climbing in meters               |
| starred              | bool     | Whether athlete has starred this       |
| pr_time              | int      | Athlete's PR time in seconds (nullable)|
| pr_date              | datetime | Date of PR (nullable)                  |
| effort_count         | int      | Athlete's total efforts on segment     |
| updated_at           | datetime | Last sync timestamp                    |

### SegmentEffort

A single attempt at a segment.

| Field             | Type     | Notes                                  |
|-------------------|----------|----------------------------------------|
| id                | int64    | Strava effort ID (primary key)         |
| segment_id        | int64    | FK to Segment                          |
| activity_id       | int64    | FK to Activity                         |
| elapsed_time      | int      | Elapsed time in seconds                |
| moving_time       | int      | Moving time in seconds                 |
| start_date        | datetime | When the effort started                |
| pr_rank           | int      | PR ranking (1=best, nullable)          |
| average_heartrate | float64  | Average HR during effort (nullable)    |
| average_watts     | float64  | Average power during effort (nullable) |

### SyncState

Tracks sync progress for incremental updates.

| Field           | Type     | Notes                                     |
|-----------------|----------|-------------------------------------------|
| id              | int64    | Auto-generated primary key                |
| entity_type     | string   | "activities", "segments", "athlete"       |
| last_sync_at    | datetime | Timestamp of last successful sync         |
| last_activity_at| datetime | Most recent activity date synced          |
| page_cursor     | int      | Pagination cursor for interrupted syncs   |
| status          | string   | "complete", "in_progress", "interrupted"  |

## Relationships

- Athlete 1:N Activity (one athlete, many activities)
- Athlete 1:N AthleteStats (one per stat_type + activity_type)
- Athlete 1:N AthleteZone (one per zone_type + zone_index)
- Activity 1:N Lap
- Activity 1:N ActivityZone
- Activity 1:N ActivityStream
- Activity N:1 Gear (many activities can use same gear)
- Activity 1:N SegmentEffort
- Segment 1:N SegmentEffort

## Storage Notes

- All distances stored in meters internally; unit conversion at display time.
- All times stored in seconds internally; formatting at display time.
- All speeds stored in m/s internally.
- Streams stored as JSON blobs for compactness.
- SQLite WAL mode enabled for concurrent read performance.
- Indexes on: Activity(athlete_id, start_date, type), Lap(activity_id),
  ActivityZone(activity_id), SegmentEffort(segment_id, activity_id).
