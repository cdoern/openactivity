# Data Model: Grade-Adjusted Pace & Effort Scoring

## Overview

This feature does **not** add new database tables or columns. All computations are performed on-the-fly from existing stream data stored in the `activity_streams` table.

## Existing Models Used

### ActivityStream (read-only)
- `activity_id`: Links to the activity
- `stream_type`: Key stream types for GAP: `"altitude"`, `"distance"`, `"time"`, `"heartrate"`
- `data`: JSON-encoded array of values (LargeBinary)

### Activity (read-only)
- `id`, `name`, `type`, `start_date`: For display and filtering
- `distance`, `moving_time`, `average_speed`: Actual pace reference
- `total_elevation_gain`: For effort score elevation component
- `average_heartrate`, `max_heartrate`: For effort score HR component

### Lap (read-only)
- `activity_id`, `lap_index`: For per-lap GAP breakdown
- `distance`, `moving_time`, `average_speed`: Per-lap actual pace
- `start_index`, `end_index`: Stream index range for per-lap GAP computation

## Computed Data Structures (not persisted)

### GAPResult
Returned by the GAP computation function for a single activity:
- `overall_gap`: float — Grade-adjusted pace in m/s
- `overall_gap_ratio`: float — Ratio of energy cost vs flat (>1 means harder than flat)
- `lap_gaps`: list of float | None — Per-lap GAP in m/s (None if lap lacks elevation data)
- `grade_profile`: list of float — Smoothed grade values across the activity
- `available`: bool — Whether GAP could be computed (requires altitude + distance streams)

### EffortScoreResult
Returned by the effort scoring function for a single activity:
- `score`: int — 0-100 composite effort score
- `duration_component`: float — Duration contribution (0-25 or 0-33.3 if no HR)
- `gap_component`: float — GAP contribution (0-25 or 0-33.3 if no HR)
- `hr_component`: float | None — HR contribution (0-25 or None if unavailable)
- `elevation_component`: float — Elevation contribution (0-25 or 0-33.3 if no HR)

### EffortTrendEntry
One row in the effort trend output:
- `activity_id`: int
- `activity_name`: str
- `date`: datetime
- `distance`: float (meters)
- `actual_pace`: float (m/s)
- `gap`: float | None (m/s)
- `effort_score`: int (0-100)
- `elevation_gain`: float (meters)
- `heartrate`: float | None (avg bpm)

### EffortTrendSummary
Aggregate summary for the effort trend:
- `trend_direction`: str — "improving", "declining", "stable"
- `avg_gap`: float — Average GAP over the window
- `avg_effort_score`: float — Average effort score
- `activity_count`: int
