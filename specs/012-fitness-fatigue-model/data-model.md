# Data Model: Fitness/Fatigue Model (ATL/CTL/TSB)

**Feature**: 012-fitness-fatigue-model
**Date**: 2026-03-24

## No Schema Changes Required

All data is computed on-the-fly from existing activity data. No new tables or columns needed.

## Computed Entities (Not Stored)

### Training Stress Score (TSS)

Computed per activity from existing fields.

| Input | Source | Required |
|-------|--------|----------|
| average_heartrate | Activity.average_heartrate | Yes |
| max_heartrate | Activity.max_heartrate | No (uses global max) |
| moving_time | Activity.moving_time (seconds) | Yes |
| max_hr (user) | max(Activity.max_heartrate) across all activities | Derived |
| rest_hr (user) | Estimated ~60 bpm or min observed avg HR | Derived |

**Output**: Float, typically 20-300+

### Daily Training Load

Aggregated from per-activity TSS values.

| Field | Description |
|-------|-------------|
| date | Calendar date |
| total_tss | Sum of TSS for all activities on this date |
| activity_count | Number of activities contributing |

### Fitness/Fatigue/Form Time Series

Computed from daily TSS using exponential decay.

| Field | Description |
|-------|-------------|
| date | Calendar date |
| tss | Daily total TSS |
| atl | Acute Training Load (7-day decay) |
| ctl | Chronic Training Load (42-day decay) |
| tsb | Training Stress Balance (CTL - ATL) |

### Training Status

Derived from current TSB and 14-day CTL trend.

| Status | Condition |
|--------|-----------|
| Peaking | CTL rising AND TSB > 5 |
| Maintaining | CTL stable (±5) AND TSB near zero (±10) |
| Overreaching | CTL rising AND TSB < -15 |
| Detraining | CTL falling (>5 drop) AND TSB > 5 |

## Data Flow

```
Activities (both providers, deduped)
  → Filter by time range and type
  → For each activity: compute TSS from HR + duration
  → Aggregate to daily TSS totals
  → Run exponential decay forward from start date
  → Output: daily ATL, CTL, TSB series
  → Classify current status from latest values + 14-day trend
```
