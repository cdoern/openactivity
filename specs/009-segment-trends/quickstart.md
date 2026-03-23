# Quickstart: Segment Trend Analysis

## Prerequisites

- Synced Strava data with segments and efforts: `openactivity strava sync`
- At least one starred segment with 3+ efforts for trend analysis

## Quick Test Scenarios

### 1. View Segment Trend (US1 - Core)

```bash
# Get a segment ID from the list
openactivity strava segments list

# View trend for a specific segment
openactivity strava segment 12345 trend
```

Expected: Trend direction, rate of change, best/worst/recent effort, effort history table.

### 2. Segments List with Trends (US2)

```bash
openactivity strava segments list
```

Expected: Trend column (↑/↓/→/—) and rate column added to existing table.

### 3. HR-Adjusted Trend (US3)

```bash
# Works automatically when efforts have HR data
openactivity strava segment 12345 trend
```

Expected: Additional "HR-Adjusted Trend" section shown when HR data is available.

### 4. JSON Output (US4)

```bash
openactivity strava segment 12345 trend --json
```

Expected: Valid JSON with trend, efforts, and HR-adjusted data.

## Edge Cases to Verify

```bash
# Segment with < 3 efforts — shows efforts, no trend
openactivity strava segment <low-effort-id> trend

# Nonexistent segment — error with sync suggestion
openactivity strava segment 99999 trend
```
