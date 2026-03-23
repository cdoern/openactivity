# Data Model: Training Block / Periodization Detector

## Overview

This feature does **not** add new database tables or columns. All computations are performed on-the-fly from existing activity data stored in the `activities` table.

## Existing Models Used

### Activity (read-only)
- `id`, `name`, `type`, `start_date`: For filtering and display
- `distance`, `moving_time`: For weekly volume computation
- `average_speed`: For pace-based intensity fallback
- `average_heartrate`, `max_heartrate`: For HR-based intensity
- `total_elevation_gain`: For display in block summaries

## Computed Data Structures (not persisted)

### WeekSummary
Aggregated metrics for a single ISO week:
- `week_start`: date — Monday of this week
- `week_end`: date — Sunday of this week
- `total_distance`: float — Sum of activity distances in meters
- `total_duration`: int — Sum of moving times in seconds
- `activity_count`: int — Number of activities
- `avg_intensity`: float — Normalized intensity score (0-100)
- `intensity_source`: str — "hr", "pace", or "default"
- `classification`: str — "recovery", "base", "build", or "peak"

### TrainingBlock
A group of consecutive weeks with the same classification:
- `phase`: str — "recovery", "base", "build", or "peak"
- `start_date`: date — Start of first week in block
- `end_date`: date — End of last week in block
- `week_count`: int — Number of weeks in the block
- `total_distance`: float — Total distance across all weeks (meters)
- `activity_count`: int — Total activities across all weeks
- `avg_weekly_distance`: float — Average weekly distance (meters)
- `avg_intensity`: float — Average intensity across weeks (0-100)
- `is_current`: bool — Whether this is the most recent block

### BlocksResult
Top-level result returned by the analysis:
- `blocks`: list[TrainingBlock] — Chronological list of detected blocks
- `weeks`: list[WeekSummary] — All weekly summaries
- `current_phase`: str — Classification of the most recent block
- `time_window`: str — The requested time window
- `activity_type`: str — The requested activity type filter
- `total_weeks`: int — Number of weeks analyzed
