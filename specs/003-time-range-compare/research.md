# Research: Custom Time-Range Comparisons

**Branch**: `003-time-range-compare` | **Date**: 2026-03-21

## Research Summary

This feature requires no new technologies, dependencies, or external integrations. All research focuses on reusing existing patterns in the codebase.

## Decisions

### 1. Aggregation Approach

**Decision**: Reuse the existing `get_activities()` query helper with `after`/`before` date filters, then aggregate in Python.

**Rationale**: The existing `analysis/summary.py` uses this exact pattern — query activities with date filters, then iterate and aggregate. The `get_activities` function already supports `after`, `before`, `activity_type`, and pagination parameters. No need for raw SQL aggregation since activity counts per range will be well under 10,000.

**Alternatives considered**:
- SQLAlchemy aggregate queries (SUM, AVG, COUNT) — would be faster for very large datasets but adds complexity for marginal gain. The existing pattern handles 10K activities in <200ms.
- New query helper — unnecessary since `get_activities` already has all needed filters.

### 2. Date Range Input Format

**Decision**: Use `YYYY-MM-DD:YYYY-MM-DD` colon-separated format for each range flag.

**Rationale**: Colon separator is unambiguous and doesn't conflict with date components. The format is ISO 8601-adjacent and parseable without additional libraries. Consistent with how date ranges are commonly expressed in CLI tools.

**Alternatives considered**:
- Two separate flags per range (`--start1`, `--end1`, `--start2`, `--end2`) — 4 flags is cumbersome.
- Slash separator (`2025-01-01/2025-03-31`) — could conflict with file paths in some shells.
- Space separator — would require quoting in shell.

### 3. Percentage Change Edge Cases

**Decision**: When range1 value is zero, display "N/A" for percentage change. When both are zero, display "—" (em dash).

**Rationale**: Division by zero is undefined. "N/A" communicates that a percentage comparison isn't meaningful. This matches how spreadsheet tools handle the same scenario.

**Alternatives considered**:
- Display "∞" or "+∞" — mathematically correct but not user-friendly.
- Display "new" — ambiguous for some metrics (e.g., zero HR doesn't mean "new").
- Omit the percentage column for that row — inconsistent table layout.

### 4. Metric Selection

**Decision**: Aggregate these metrics: activity count, total distance, total moving time, total elevation gain, average pace (run/walk/hike only), average speed (ride only), average heart rate (when available).

**Rationale**: These match the metrics already computed by `analysis/summary.py` with the addition of average pace/speed and HR. Pace and speed are type-dependent — pace is meaningful for foot-based activities, speed for cycling.

**Alternatives considered**:
- Include max HR, calories, suffer score — these are less useful for period comparison and add noise.
- Include per-activity breakdown — that's a different feature (activity list with filters already exists).
