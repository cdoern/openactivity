# Feature Specification: Cross-Activity Correlation Engine

**Feature Branch**: `008-correlation-engine`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Correlate any two metrics across activities to find training patterns with lag analysis."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Correlate Two Weekly Metrics (Priority: P1)

As a data-driven athlete, I want to correlate any two weekly training metrics to discover patterns in my data, so I can understand which aspects of my training influence my performance.

The user runs `openactivity strava analyze correlate --x weekly_distance --y avg_pace --last 1y` and sees the Pearson and Spearman correlation coefficients, p-values, strength label, and the data points used.

**Why this priority**: This is the core value — computing and displaying a correlation between two metrics. Everything else builds on this.

**Independent Test**: Run `openactivity strava analyze correlate --x weekly_distance --y avg_pace` and verify correlation results are displayed with statistical significance.

**Acceptance Scenarios**:

1. **Given** the user has 12+ weeks of synced running data, **When** they run `correlate --x weekly_distance --y avg_pace --last 1y`, **Then** they see Pearson and Spearman correlation coefficients, p-values, a strength label (weak/moderate/strong), sample size, and a summary of the data points.
2. **Given** the user specifies an unsupported metric name, **When** they run `correlate --x invalid_metric --y avg_pace`, **Then** they see an error listing all supported metric names.
3. **Given** the user has fewer than 4 weeks of data, **When** they run `correlate`, **Then** they see an informative message that more data is needed for meaningful correlation.

---

### User Story 2 - Lag Analysis (Priority: P2)

As a coach or self-coached athlete, I want to see if a metric from this week predicts a different metric in future weeks, so I can understand delayed training effects (e.g., "does this week's mileage predict next month's pace?").

The user runs `correlate --x weekly_distance --y avg_pace --lag 4` and sees how this week's distance correlates with pace 4 weeks later.

**Why this priority**: Lag analysis is the unique differentiator — no consumer platform offers this. But it requires the base correlation to work first.

**Independent Test**: Run with `--lag 4` and verify the correlation uses offset data correctly.

**Acceptance Scenarios**:

1. **Given** the user has 16+ weeks of data, **When** they run `correlate --x weekly_distance --y avg_pace --lag 4`, **Then** the correlation compares week N distance with week N+4 pace, and the output clearly states the lag.
2. **Given** a lag of 0, **When** the user runs `correlate --lag 0`, **Then** the behavior is identical to no lag (same-week correlation).

---

### User Story 3 - JSON Output for Agents (Priority: P3)

As an AI agent, I want structured JSON output from the correlate command, so I can programmatically discover which training factors most predict performance improvement.

The user runs `openactivity --json strava analyze correlate --x weekly_distance --y avg_pace` and gets structured JSON.

**Why this priority**: Follows the established JSON pattern for agent consumption.

**Independent Test**: Run with `--json` flag and verify valid JSON containing all correlation data.

**Acceptance Scenarios**:

1. **Given** the `--json` flag is active, **When** the user runs `correlate --x weekly_distance --y avg_pace`, **Then** the output is valid JSON containing `pearson_r`, `pearson_p`, `spearman_r`, `spearman_p`, `strength`, `sample_size`, `lag`, and `data_points` array.
2. **Given** insufficient data with `--json`, **When** the user runs `correlate`, **Then** the output is valid JSON with an `error` field.

---

### Edge Cases

- What happens when one or both metrics have zero variance (all identical values)? The system reports that correlation cannot be computed and explains why.
- What happens when the lag exceeds available data? The system shows an error explaining that lag N requires at least N + 4 weeks of data.
- What happens when metrics have missing values for some weeks (e.g., no HR data)? Weeks with missing values for either metric are excluded, and the system reports how many weeks were usable vs total.
- What happens when the user correlates a metric with itself? The system computes it (will be r=1.0) but notes that self-correlation is expected.
- What happens with very few data points (4-8 weeks)? The system warns that results may not be statistically significant due to small sample size.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute Pearson correlation coefficient (r) and p-value for any two supported weekly metrics.
- **FR-002**: System MUST compute Spearman rank correlation coefficient (rho) and p-value as a non-parametric alternative.
- **FR-003**: System MUST support the following weekly metrics: `weekly_distance`, `weekly_duration`, `weekly_elevation`, `avg_pace`, `avg_hr`, `max_hr`, `activity_count`, `rest_days`, `longest_run`.
- **FR-004**: System MUST assign a strength label based on the absolute correlation coefficient: weak (|r| < 0.3), moderate (0.3 ≤ |r| < 0.7), strong (|r| ≥ 0.7).
- **FR-005**: System MUST support a `--lag` flag accepting integer values 0, 1, 2, and 4 (weeks) to offset Y-metric data relative to X-metric data.
- **FR-006**: System MUST support a `--last` flag for time window filtering, accepting values like "6m", "1y", "all" (default: "1y").
- **FR-007**: System MUST support a `--type` flag (default: "Run") to filter activities by type.
- **FR-008**: System MUST require at least 4 usable data points (weeks with both metrics present) to compute correlation.
- **FR-009**: System MUST display the number of usable weeks vs total weeks when some weeks have missing data.
- **FR-010**: System MUST display a direction interpretation alongside the coefficient (e.g., "More weekly distance is associated with faster pace").
- **FR-011**: System MUST produce valid JSON output when the global `--json` flag is active, containing all correlation data and the underlying data points.
- **FR-012**: System MUST show an informative error when an unsupported metric name is provided, listing all valid options.
- **FR-013**: System MUST display statistical significance: if p-value > 0.05, note that the result is not statistically significant.

### Key Entities

- **WeeklyMetrics**: A single week's computed metrics — all supported metric values aggregated from that week's activities. One row per ISO week.
- **CorrelationResult**: The output of a correlation computation — includes Pearson r and p, Spearman rho and p, strength label, direction interpretation, sample size, lag, and the paired data points.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can correlate any two supported metrics and see results in under 5 seconds.
- **SC-002**: Correlation output includes both Pearson and Spearman coefficients with p-values so users can assess reliability.
- **SC-003**: Lag analysis correctly offsets data by the specified number of weeks, enabling delayed-effect discovery.
- **SC-004**: Users with insufficient data receive clear guidance on how much more data is needed.
- **SC-005**: JSON output contains all fields needed for an agent to rank which factors most predict a target metric.
- **SC-006**: Statistical significance (p < 0.05) is clearly indicated so users do not over-interpret weak correlations.

## Assumptions

- Weekly aggregation uses ISO weeks (Monday-Sunday), consistent with the existing blocks system.
- `rest_days` is computed as 7 minus the number of days with at least one activity in that week.
- `longest_run` is the maximum single-activity distance in a given week.
- `avg_pace` is the distance-weighted average pace across all activities in the week.
- `avg_hr` and `max_hr` are only computed from activities that have heart rate data; weeks with no HR data have these metrics marked as missing.
- `zone2_pct` and `zone4_pct` from the roadmap are excluded from MVP scope because zone data requires athlete zone configuration which not all users have. These can be added later.
- The Pearson correlation assumes a linear relationship; Spearman is included as a non-parametric alternative for non-linear patterns.
- Minimum 4 data points is a statistical floor; the system warns about low confidence below 12 data points.
