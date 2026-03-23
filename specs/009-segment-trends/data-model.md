# Data Model: Segment Trend Analysis

No new database tables or schema changes. This feature computes analysis on-the-fly from existing data.

## Existing Entities Used

### Segment (read-only)

| Field | Type | Notes |
|-------|------|-------|
| id | Integer (PK) | Strava segment ID |
| name | String | Segment name |
| distance | Float | Distance in meters |
| activity_type | String | "Run", "Ride" |
| effort_count | Integer | Total efforts synced |
| pr_time | Integer (nullable) | Best time in seconds |
| starred | Boolean | Whether athlete starred it |

### SegmentEffort (read-only)

| Field | Type | Notes |
|-------|------|-------|
| id | Integer (PK) | Strava effort ID |
| segment_id | Integer (FK) | Links to Segment |
| elapsed_time | Integer | Effort time in seconds |
| start_date | DateTime (nullable) | When the effort occurred |
| average_heartrate | Float (nullable) | Avg HR during effort |
| pr_rank | Integer (nullable) | PR ranking (1 = current PR) |

## Computed Entities (not persisted)

### SegmentTrend

Computed result of trend analysis on a segment's efforts.

| Field | Type | Notes |
|-------|------|-------|
| segment_id | Integer | Which segment |
| segment_name | String | For display |
| direction | String | "improving" / "declining" / "stable" |
| rate_of_change | Float | Seconds per month (negative = improving) |
| r_squared | Float | Goodness of fit (0-1) |
| effort_count | Integer | Number of efforts analyzed |
| date_range_start | DateTime | First effort date |
| date_range_end | DateTime | Most recent effort date |
| best_effort | EffortSummary | Fastest effort |
| worst_effort | EffortSummary | Slowest effort |
| recent_effort | EffortSummary | Most recent effort |
| hr_adjusted | HRAdjustedTrend (nullable) | If HR data available |

### EffortSummary

Summary of a single effort for display.

| Field | Type | Notes |
|-------|------|-------|
| date | DateTime | When the effort occurred |
| elapsed_time | Integer | Time in seconds |
| average_heartrate | Float (nullable) | Avg HR |
| delta_from_best | Integer | Seconds slower than best |
| hr_normalized_time | Float (nullable) | elapsed_time / avg_hr |

### HRAdjustedTrend

HR-adjusted trend computed separately from raw trend.

| Field | Type | Notes |
|-------|------|-------|
| direction | String | "improving" / "declining" / "stable" |
| rate_of_change | Float | Normalized units per month |
| r_squared | Float | Goodness of fit |
| effort_count | Integer | Efforts with HR data (may be fewer) |
