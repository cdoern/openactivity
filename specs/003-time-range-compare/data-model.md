# Data Model: Custom Time-Range Comparisons

**Branch**: `003-time-range-compare` | **Date**: 2026-03-21

## Overview

This feature introduces no new persisted entities. All data is computed on the fly from the existing `Activity` model. Two transient data structures are used for computation and output.

## Existing Entities Used

### Activity (read-only)

The comparison queries the existing `activities` table using these fields:

| Field | Type | Usage |
|-------|------|-------|
| start_date_local | datetime | Filter activities within each date range |
| type | string | Filter by activity type (Run, Ride, etc.) |
| distance | float | Sum for total distance (meters) |
| moving_time | int | Sum for total moving time (seconds) |
| elevation_gain | float | Sum for total elevation gain (meters) |
| average_speed | float | Used to compute average pace/speed |
| average_heartrate | float | Average across activities with HR data |
| has_heartrate | bool | Filter activities that have HR data |

## Transient Data Structures

### RangeMetrics

Aggregated metrics for a single date range. Not persisted.

| Field | Type | Description |
|-------|------|-------------|
| start_date | date | Range start (inclusive) |
| end_date | date | Range end (inclusive) |
| count | int | Number of activities |
| distance | float | Total distance (meters) |
| moving_time | int | Total moving time (seconds) |
| elevation_gain | float | Total elevation gain (meters) |
| avg_pace | float or None | Average pace in sec/meter (foot-based types only) |
| avg_speed | float or None | Average speed in m/s (cycling types only) |
| avg_heartrate | float or None | Average HR (activities with HR only) |

### RangeComparison

The complete comparison result. Not persisted.

| Field | Type | Description |
|-------|------|-------------|
| range1 | RangeMetrics | Metrics for the first date range |
| range2 | RangeMetrics | Metrics for the second date range |
| deltas | dict | range2 - range1 for each numeric metric |
| pct_changes | dict | Percentage change for each metric (None when range1 is zero) |
| activity_type | string or None | Type filter applied (None if unfiltered) |
| overlap_warning | bool | True if date ranges overlap |

## Relationships

```
Activity (existing) --[queried by date range]--> RangeMetrics (computed)
RangeMetrics x 2 --> RangeComparison (computed)
```

No new database tables, columns, indexes, or migrations required.
