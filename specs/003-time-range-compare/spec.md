# Feature Specification: Custom Time-Range Comparisons

**Feature Branch**: `003-time-range-compare`
**Created**: 2026-03-21
**Status**: Draft
**Input**: User description: "Compare any two arbitrary date ranges across all metrics. Strava only offers YTD vs prior year. New command openactivity strava analyze compare with --range1 and --range2 flags. Optional --type filter. Side-by-side table with deltas and percentage change. JSON output for agent consumption."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare Two Training Periods (Priority: P1)

A user wants to compare their training volume and performance across two date ranges to understand how their fitness has changed over time. They run a compare command specifying two arbitrary ranges and see a side-by-side table showing totals and averages for each period, with deltas and percentage changes. This answers questions like "Am I training more this quarter than last quarter?" or "How does my winter base compare year-over-year?"

**Why this priority**: This is the core value proposition — arbitrary range comparison is something Strava doesn't offer. Without this, the feature has no purpose.

**Independent Test**: Can be fully tested by syncing activities spanning two date ranges, running the compare command with those ranges, and verifying the output table shows correct aggregated metrics with accurate deltas and percentage changes.

**Acceptance Scenarios**:

1. **Given** a user with synced activities in both date ranges, **When** they run the compare command with two ranges, **Then** they see a side-by-side table with totals and averages for each range plus delta and percentage change columns.
2. **Given** a user with activities in only one of the two ranges, **When** they run the compare command, **Then** the empty range shows zeroes and the delta reflects the full values from the populated range.
3. **Given** a user specifying overlapping ranges, **When** they run the compare command, **Then** the system warns that ranges overlap and still produces results.
4. **Given** a user who provides an invalid date format or a range where the start date is after the end date, **When** they run the compare command, **Then** they see a clear error message explaining the expected format.

---

### User Story 2 - Filter Comparison by Activity Type (Priority: P2)

A user wants to compare only a specific activity type (e.g., running or cycling) across two periods. They add a type filter so the comparison reflects only the activities they care about, since mixing running and cycling metrics together is often meaningless.

**Why this priority**: Type filtering makes the comparison actionable for users who train across multiple sports.

**Independent Test**: Can be tested by running the compare command with a type filter and verifying that only activities of that type are included in both ranges' aggregations.

**Acceptance Scenarios**:

1. **Given** a user with both runs and rides in each range, **When** they run the compare command with a type filter for running, **Then** only running activities are included in the comparison.
2. **Given** a user filtering by a type with no activities in either range, **When** they run the compare command, **Then** they see a message indicating no activities matched the filter.

---

### User Story 3 - JSON Output for Agent Consumption (Priority: P3)

An AI agent or script wants to programmatically consume comparison data. The user or agent requests structured output that can be parsed and reasoned about to answer questions like "Am I training more or less than last year at this point?"

**Why this priority**: JSON output enables the agent-first use case, which is a core goal of the project.

**Independent Test**: Can be tested by running the compare command with a JSON flag and verifying the output is valid JSON containing both ranges' metrics, deltas, and percentage changes.

**Acceptance Scenarios**:

1. **Given** a user running the compare command with JSON output, **When** the command completes, **Then** the output is valid JSON containing range1 metrics, range2 metrics, deltas, and percentage changes for all metrics.
2. **Given** a user running with both JSON output and a type filter, **When** the command completes, **Then** the JSON reflects the filtered data and includes metadata about the filter applied.

---

### Edge Cases

- What happens when one or both ranges contain zero activities? The comparison should render with zeroes for the empty range.
- What happens when ranges span periods before the user started using the platform? The comparison should use whatever data exists without erroring.
- What happens when ranges are identical? The comparison should show identical values on both sides with zero deltas.
- How does the system handle very large ranges with thousands of activities? The comparison should complete within a reasonable time by computing aggregates from local data.
- What happens with pace metrics when no pace-relevant activities exist? Pace should show as "N/A" rather than zero.
- What happens when range1 metrics are zero and range2 has values? Percentage change should display as "new" or "N/A" rather than infinity.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept two date ranges in `YYYY-MM-DD:YYYY-MM-DD` format via two required range flags.
- **FR-002**: System MUST validate that each range has a valid start and end date, with start before or equal to end.
- **FR-003**: System MUST aggregate the following metrics for each range: total activity count, total distance, total moving time, total elevation gain, average pace (for pace-relevant activity types), and average heart rate (when HR data exists).
- **FR-004**: System MUST compute the delta (range2 minus range1) and percentage change for each metric.
- **FR-005**: System MUST display results as a formatted table with columns: Metric, Range 1, Range 2, Delta, and Change %.
- **FR-006**: System MUST support an optional type flag to filter by activity type (e.g., Run, Ride, Swim).
- **FR-007**: System MUST support structured JSON output containing all computed metrics, deltas, percentages, and metadata (ranges used, filters applied).
- **FR-008**: System MUST display direction indicators in the table output (e.g., arrows or +/- signs) to show whether a metric increased or decreased.
- **FR-009**: System MUST respect the user's configured unit system (metric or imperial) when displaying distance, elevation, and pace values.
- **FR-010**: System MUST warn (not error) when ranges overlap, noting that shared activities contribute to both sides.
- **FR-011**: Both range flags MUST be required — the command should error with a helpful message if either is missing.

### Key Entities

- **RangeComparison**: A computed result containing two sets of aggregated metrics (one per range), their deltas, and percentage changes. Not persisted — computed on the fly from existing activity data.
- **RangeMetrics**: Aggregated metrics for a single date range — count, distance, duration, elevation, average pace, average heart rate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can compare any two date ranges and see results within 2 seconds for up to 5,000 activities.
- **SC-002**: All numeric metrics show accurate deltas and percentage changes matching manual calculation.
- **SC-003**: JSON output is valid and parseable, containing all metrics present in the table view.
- **SC-004**: Users with no activities in one or both ranges receive a clear, non-error response showing zeroes for empty ranges.
- **SC-005**: The comparison respects unit preferences — users see values in their configured unit system.

## Assumptions

- Date ranges are inclusive of both start and end dates.
- "Average pace" applies only to activity types where pace is meaningful (running, walking, hiking). For cycling, average speed is used instead.
- "Average HR" is computed only from activities with heart rate data; activities without HR are excluded from the HR average rather than counted as zero.
- The command operates entirely on locally synced data — no network calls are made.
- The percentage change formula is: ((range2 - range1) / range1) * 100. When range1 is zero, percentage is shown as "N/A" rather than infinity.
