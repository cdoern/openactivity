# Quickstart: Custom Time-Range Comparisons

## Prerequisites

- openactivity installed and authenticated (`openactivity strava auth`)
- Activities synced to local database (`openactivity strava sync`)

## Compare Two Periods

```bash
# Compare this quarter to the same quarter last year
openactivity strava analyze compare \
  --range1 2025-01-01:2025-03-31 \
  --range2 2026-01-01:2026-03-31
```

## Filter by Activity Type

```bash
# Compare only running activities
openactivity strava analyze compare \
  --range1 2025-01-01:2025-03-31 \
  --range2 2026-01-01:2026-03-31 \
  --type Run
```

## JSON Output for Agents

```bash
# Get structured data for programmatic use
openactivity strava analyze compare \
  --range1 2025-06-01:2025-08-31 \
  --range2 2026-06-01:2026-08-31 \
  --json
```

## Common Comparisons

```bash
# Month-over-month
openactivity strava analyze compare \
  --range1 2026-01-01:2026-01-31 \
  --range2 2026-02-01:2026-02-28

# Summer vs winter training
openactivity strava analyze compare \
  --range1 2025-12-01:2026-02-28 \
  --range2 2025-06-01:2025-08-31

# Imperial units
openactivity strava analyze compare \
  --range1 2025-01-01:2025-06-30 \
  --range2 2026-01-01:2026-06-30 \
  --units imperial
```
