# Data Model: Recovery & Readiness Score

## No Schema Changes Required

This feature computes readiness scores on-the-fly from existing data. No new tables or columns needed.

## Existing Entities Used

### GarminDailySummary (existing table)
| Field | Type | Used For |
|-------|------|----------|
| date | Date | Day lookup |
| hrv_avg | Integer (nullable) | HRV component — compare to 7-day baseline |
| sleep_score | Integer (nullable) | Sleep component — direct 0-100 mapping |
| body_battery_max | Integer (nullable) | HRV component modifier (supplementary) |
| stress_avg | Integer (nullable) | HRV component modifier (supplementary) |

### Activity (existing table)
| Field | Type | Used For |
|-------|------|----------|
| start_date | DateTime | Volume trend — filter activities by date range |
| distance | Float | Volume trend — sum distances per 7-day window |
| moving_time | Integer | TSS computation via fitness model |
| average_heartrate | Float | TSS computation via fitness model |

### Computed: Daily TSB (from fitness model, not stored)
| Field | Type | Used For |
|-------|------|----------|
| date | String (ISO) | Day lookup |
| tsb | Float | Form component — map to 0-100 score |

## Computed Entity: DailyReadiness (not stored)

Returned by `compute_readiness()`, one per requested day:

| Field | Type | Description |
|-------|------|-------------|
| date | date | Calendar date |
| score | int | Composite readiness 0-100 |
| label | str | "Go Hard" / "Easy Day" / "Rest" |
| recommendation | str | Human-readable recommendation text |
| components | dict | Per-component breakdown (see below) |

### Component Structure

Each component in `components` dict:

| Field | Type | Description |
|-------|------|-------------|
| name | str | "hrv", "sleep", "form", "volume" |
| score | int | Component score 0-100 |
| weight | float | Effective weight (after redistribution) |
| available | bool | Whether data was present |
| description | str | Human-readable explanation |
