# Feature Specification: Grade-Adjusted Pace & Effort Scoring

**Feature Branch**: `005-gap-effort`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Compute Grade-Adjusted Pace from elevation and distance streams so users can compare efforts across hilly vs flat courses. Strava shows GAP per-activity but doesn't let you trend it or compare across activities. Add a normalized effort score per activity. Extend `openactivity strava activity <ID>` detail view with GAP per split and overall. New command: `openactivity strava analyze effort` — trend GAP over time. Algorithm: Apply Minetti energy cost model to grade stream, compute equivalent flat pace. Effort score: normalize each activity to a 0-100 scale based on duration, GAP, HR, and elevation. Enables fair comparison: a hilly trail run vs a flat road run. `--json` output for agents."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Grade-Adjusted Pace for a Single Activity (Priority: P1)

A runner wants to understand their true effort on a hilly run. They view a single activity's details and see Grade-Adjusted Pace (GAP) for the overall activity and per split/lap. This tells them "if I ran this same effort on a flat course, my pace would have been X." They can now fairly compare a hilly trail run to a flat road run.

**Why this priority**: GAP computation is the foundational capability — every other feature builds on it. Seeing GAP per-activity is the most immediate, concrete value.

**Independent Test**: Can be tested by viewing a synced activity with elevation data and verifying that GAP values appear in the activity detail output alongside actual pace.

**Acceptance Scenarios**:

1. **Given** a user with a synced running activity that has elevation and distance stream data, **When** they view the activity detail, **Then** they see overall GAP displayed alongside actual pace.
2. **Given** a user viewing an activity with lap data, **When** the activity has elevation stream data, **Then** each lap/split shows both actual pace and GAP.
3. **Given** a flat run with minimal elevation change, **When** the user views GAP, **Then** GAP is approximately equal to actual pace (within 5 seconds/mile).
4. **Given** an activity without elevation stream data, **When** the user views the activity, **Then** GAP shows as unavailable rather than erroring.

---

### User Story 2 - Trend GAP Over Time (Priority: P2)

A runner wants to see if their flat-equivalent effort is improving over time, independent of which routes they ran. They run a command to see their GAP trend across recent activities. This reveals true fitness improvement that actual pace alone can't show (because actual pace varies based on terrain).

**Why this priority**: Trending GAP over time is the key differentiator over Strava — it answers "Am I getting faster?" independent of route selection.

**Independent Test**: Can be tested by running the effort trend command and verifying a chronological list of activities with their GAP values, trend direction, and summary statistics.

**Acceptance Scenarios**:

1. **Given** a user with multiple running activities over time, **When** they run the effort trend command, **Then** they see a table of activities with date, actual pace, GAP, effort score, and elevation gain.
2. **Given** a user who filters by time window, **When** they use `--last 90d`, **Then** only activities within the last 90 days appear.
3. **Given** a user who filters by activity type, **When** they use `--type Run`, **Then** only running activities appear.
4. **Given** a user with no activities in the specified window, **When** they run the command, **Then** they see a message indicating no matching activities.

---

### User Story 3 - Effort Score for Fair Comparison (Priority: P3)

A runner wants a single number to compare how hard different workouts were, regardless of terrain, distance, or duration. They see an effort score (0-100) per activity that accounts for duration, GAP, heart rate, and elevation. This lets them answer: "Which was my hardest workout this month?"

**Why this priority**: Effort scoring builds on GAP (US1) and adds a composite metric. It's valuable but requires the foundational GAP computation to exist first.

**Independent Test**: Can be tested by viewing effort scores for a set of activities with varying terrain/duration and verifying that harder efforts (longer duration, faster GAP, higher HR, more elevation) produce higher scores.

**Acceptance Scenarios**:

1. **Given** a user with multiple activities of varying difficulty, **When** they view the effort trend, **Then** each activity shows an effort score from 0 to 100.
2. **Given** two runs of similar distance where one is hilly with higher HR, **When** the user compares effort scores, **Then** the harder run has a higher effort score.
3. **Given** an activity without heart rate data, **When** the effort score is computed, **Then** the score is still calculated using the available metrics (duration, GAP, elevation) without erroring.
4. **Given** a very short easy jog, **When** the effort score is computed, **Then** the score is low (near 0-20 range).

---

### User Story 4 - JSON Output for Agent Consumption (Priority: P4)

An AI agent or script wants to programmatically query GAP and effort data. All commands support structured JSON output so agents can answer questions like "What was my hardest effort this month?" or "Is my GAP improving over time?"

**Why this priority**: JSON output enables agent-first use cases. It depends on the data being computed from US1/US2/US3.

**Independent Test**: Can be tested by running any GAP/effort command with the JSON flag and verifying valid, parseable JSON output.

**Acceptance Scenarios**:

1. **Given** a user running the activity detail command with JSON output, **When** the activity has GAP data, **Then** the JSON includes GAP fields alongside existing activity fields.
2. **Given** a user running the effort trend command with JSON output, **When** the command completes, **Then** the output is valid JSON containing all activities with GAP, effort score, and trend data.

---

### Edge Cases

- What happens when an activity has elevation data but no distance stream? GAP cannot be computed — show as unavailable.
- What happens with treadmill runs that have no elevation data? Effort score should still be computed using available metrics (duration, pace, HR), with GAP equal to actual pace (flat assumed).
- What happens with very short activities (e.g., <0.5 miles)? They should still get GAP computed but may not contribute meaningfully to effort scoring — include them but don't let them skew trend analysis.
- What happens when elevation stream data is noisy or has gaps? Apply smoothing to the grade computation to avoid extreme spikes in the energy cost model.
- What happens with negative splits on a downhill? The Minetti model handles negative grades — downhill effort is lower than flat, so GAP will be faster than actual pace.
- How does the system handle activities with paused segments? Use moving time for pace calculations, consistent with the rest of the system.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute Grade-Adjusted Pace for running activities using the Minetti energy cost model applied to grade (slope) data derived from elevation and distance streams.
- **FR-002**: System MUST display overall GAP in the activity detail view alongside actual pace.
- **FR-003**: System MUST display per-lap/split GAP in the activity detail view when lap data is available.
- **FR-004**: System MUST provide an effort trend command that shows GAP and effort score across activities over a configurable time window.
- **FR-005**: System MUST support time window filtering on the effort trend command (e.g., last 90 days, 6 months, 1 year).
- **FR-006**: System MUST support activity type filtering on the effort trend command (default: Run).
- **FR-007**: System MUST compute an effort score (0-100) per activity based on duration, GAP, heart rate (when available), and total elevation gain.
- **FR-008**: System MUST gracefully handle missing elevation stream data by omitting GAP rather than erroring.
- **FR-009**: System MUST handle missing heart rate data by computing effort score from the remaining available metrics.
- **FR-010**: System MUST apply smoothing to elevation/grade data to handle noise in stream data before computing GAP.
- **FR-011**: System MUST support structured JSON output on all GAP and effort-related commands for programmatic consumption.
- **FR-012**: System MUST respect the user's configured unit system when displaying pace values (min/km or min/mi).
- **FR-013**: System MUST show trend direction (improving, declining, stable) in the effort trend output based on GAP over the selected time window.

### Key Entities

- **GradeAdjustedPace**: The equivalent flat-ground pace for a given activity or segment, computed by applying the Minetti energy cost model to the grade profile. Attributes: overall GAP (pace value), per-lap GAP values, grade profile summary.
- **EffortScore**: A normalized 0-100 score representing the overall difficulty of an activity. Attributes: score value, component weights (duration, GAP, HR, elevation), contributing factors breakdown.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: GAP computation for a single activity with stream data completes within 1 second.
- **SC-002**: Effort trend across 500 activities returns results within 5 seconds.
- **SC-003**: GAP for a flat run (< 50m total elevation gain) is within 5 seconds/mile of actual pace.
- **SC-004**: Effort scores are consistently ordered — harder efforts (longer, faster GAP, higher HR, more elevation) always produce higher scores than easier efforts.
- **SC-005**: All commands produce valid, parseable JSON when the JSON flag is used.
- **SC-006**: Activities without elevation data display gracefully without errors.
- **SC-007**: GAP and effort score are displayed for all activity types that have the required stream data.

## Assumptions

- Elevation streams contain altitude data in meters at the same resolution as distance streams.
- The Minetti energy cost model uses the relationship between grade (slope percentage) and metabolic cost to compute equivalent flat-ground pace. The standard Minetti cost function: C(grade) = 155.4*grade^5 - 30.4*grade^4 - 43.3*grade^3 + 46.3*grade^2 + 19.5*grade + 3.6 (J/kg/m).
- Grade is computed as rise/run from consecutive elevation and distance stream points.
- Effort score weighting: duration (25%), GAP relative to personal baseline (25%), heart rate relative to max HR or threshold (25%), elevation gain per distance (25%). If HR is unavailable, redistribute its weight equally among the other three factors.
- Activities with fewer than 10 stream data points are too short for reliable GAP computation and should be excluded.
- The system does not persist GAP or effort scores — they are computed on-the-fly from stream data. This avoids schema changes and keeps data fresh.
- Trend direction is determined by linear regression on GAP values over the selected time window: improving (negative slope > threshold), declining (positive slope > threshold), stable (within threshold).
