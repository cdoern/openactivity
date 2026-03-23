# Data Model: Cross-Activity Correlation Engine

**Note**: All entities are computed on-the-fly. No new database tables or schema changes.

## Computed Entities

### WeeklyMetrics

A single ISO week's aggregated metrics, computed from that week's activities.

| Field | Type | Description |
|-------|------|-------------|
| week_key | str | ISO week identifier (e.g., "2026-W12") |
| week_start | datetime | Monday of the week |
| weekly_distance | float | Total distance in meters |
| weekly_duration | int | Total moving time in seconds |
| weekly_elevation | float | Total elevation gain in meters |
| avg_pace | float or None | Distance-weighted average pace (seconds/km) |
| avg_hr | float or None | Activity-weighted average heart rate (None if no HR data) |
| max_hr | float or None | Maximum heart rate across all activities (None if no HR data) |
| activity_count | int | Number of activities |
| rest_days | int | 7 minus number of days with at least one activity |
| longest_run | float | Maximum single-activity distance in meters |

**Source**: Computed from Activity records via `aggregate_weeks()` + per-metric functions.

### CorrelationResult

The output of a correlation computation between two metrics.

| Field | Type | Description |
|-------|------|-------------|
| x_metric | str | Name of the X metric |
| y_metric | str | Name of the Y metric |
| pearson_r | float | Pearson correlation coefficient (-1 to 1) |
| pearson_p | float | Pearson p-value |
| spearman_r | float | Spearman rank correlation coefficient (-1 to 1) |
| spearman_p | float | Spearman p-value |
| strength | str | "weak", "moderate", or "strong" |
| direction | str | Human-readable interpretation (e.g., "More distance → faster pace") |
| significant | bool | True if p-value < 0.05 |
| sample_size | int | Number of usable week pairs |
| total_weeks | int | Total weeks in time window |
| lag | int | Lag offset in weeks |
| data_points | list[dict] | Paired (x, y, week_key) values used |

## Supported Metrics Registry

| Metric Name | Description | Can Be Missing |
|-------------|-------------|----------------|
| weekly_distance | Total distance (meters) | No |
| weekly_duration | Total moving time (seconds) | No |
| weekly_elevation | Total elevation gain (meters) | No |
| avg_pace | Distance-weighted avg pace (s/km) | No |
| avg_hr | Avg heart rate across activities | Yes (no HR data) |
| max_hr | Max heart rate in week | Yes (no HR data) |
| activity_count | Number of activities | No |
| rest_days | Days without activity (0-7) | No |
| longest_run | Max single-activity distance | No |

## Relationships

```
CorrelationResult
├── x_metric → WeeklyMetrics[x_metric] for each week
├── y_metric → WeeklyMetrics[y_metric] for each week (offset by lag)
└── data_points[] → paired values from WeeklyMetrics
```

## Reused Models (no changes)

- **Activity** (`db/models.py`): Source data — distance, time, HR, speed, elevation, start_date
- **WeekSummary** (computed in `analysis/blocks.py`): Base weekly aggregation reused and extended with additional metrics
