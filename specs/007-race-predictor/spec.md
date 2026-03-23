# Feature Specification: Race Predictor & Readiness Score

**Feature Branch**: `007-race-predictor`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Predict race times at target distances using recent training data, PR history, and current fitness. Riegel formula adjusted for training context. Readiness score 0-100."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Predict Race Time for a Target Distance (Priority: P1)

As a runner preparing for a race, I want to see a predicted finish time for my target distance based on my recent best efforts, so I can set realistic goals and plan my pacing strategy.

The user runs `openactivity strava predict --distance 10K` and sees a predicted finish time, pace, and confidence range derived from their recent shorter-distance performances using the Riegel formula.

**Why this priority**: This is the core value proposition — race time prediction. Without this, the feature has no purpose.

**Independent Test**: Run `openactivity strava predict --distance 10K` with synced activity data containing recent best efforts. Verify a predicted time, pace, and confidence interval are displayed.

**Acceptance Scenarios**:

1. **Given** the user has synced activities with at least 2 best efforts at distances shorter than the target, **When** they run `predict --distance 10K`, **Then** they see a predicted finish time, predicted pace, and a confidence range (e.g., "42:30 - 44:15").
2. **Given** the user has no recent activity data, **When** they run `predict --distance 10K`, **Then** they see an informative message explaining insufficient data is available.
3. **Given** the user requests a distance they have already raced, **When** they run `predict --distance 5K`, **Then** the prediction still works using other reference distances and their actual PR is shown alongside for comparison.

---

### User Story 2 - View Readiness Score (Priority: P2)

As a runner with an upcoming race, I want to see a readiness score (0-100) that tells me how prepared I am based on my recent training patterns, so I can decide if I need to adjust my training or expectations.

The user runs `openactivity strava predict --distance half` and, alongside the time prediction, sees a readiness score with a breakdown showing training consistency, volume trend, taper status, and PR recency.

**Why this priority**: Readiness adds actionable context to the raw prediction — it answers "am I ready?" not just "what could I run?"

**Independent Test**: Run `predict --distance half` and verify a readiness score (0-100) is shown with a labeled breakdown of its components.

**Acceptance Scenarios**:

1. **Given** the user has 8+ weeks of consistent training data, **When** they run `predict --distance half`, **Then** they see a readiness score with 4 component scores: training consistency, volume trend, taper status, and PR recency.
2. **Given** the user has been training inconsistently (many gaps), **When** they run `predict`, **Then** the readiness score reflects low consistency and the breakdown explains why.
3. **Given** the user is in a taper phase (volume declining last 2+ weeks with maintained intensity), **When** they run `predict`, **Then** the taper status component scores high, indicating race readiness.

---

### User Story 3 - Race-Date Countdown with Adjusted Prediction (Priority: P3)

As a runner with a specific race date, I want to provide my race date so the prediction accounts for remaining training time, so I can see how my fitness might change by race day.

The user runs `openactivity strava predict --distance marathon --race-date 2026-06-15` and sees the prediction contextualized to that date — days until race, current training phase, and whether they are on track.

**Why this priority**: Adds temporal context but the core prediction works without it.

**Independent Test**: Run `predict --distance marathon --race-date 2026-06-15` and verify the output includes days until race and training phase context.

**Acceptance Scenarios**:

1. **Given** a race date is provided, **When** the user runs `predict --distance marathon --race-date 2026-06-15`, **Then** the output shows days until race, current training phase, and whether volume trend aligns with expected taper timing.
2. **Given** the race date is in the past, **When** the user provides it, **Then** the system shows an error message.

---

### User Story 4 - JSON Output for Agents (Priority: P4)

As an AI agent or script consumer, I want structured JSON output from the predict command, so I can build training plans or race-day strategies programmatically.

The user runs `openactivity --json strava predict --distance 10K` and gets structured JSON with all prediction data.

**Why this priority**: Follows the established pattern for agent consumption but is not user-facing.

**Independent Test**: Run with `--json` flag and verify valid JSON output containing prediction, readiness, and metadata fields.

**Acceptance Scenarios**:

1. **Given** the `--json` flag is active, **When** the user runs `predict --distance 10K`, **Then** the output is valid JSON containing `predicted_time`, `predicted_pace`, `confidence_range`, `readiness_score`, `readiness_breakdown`, and `reference_efforts`.
2. **Given** insufficient data with `--json`, **When** the user runs `predict`, **Then** the output is valid JSON with an `error` field and descriptive message.

---

### Edge Cases

- What happens when the user has only 1 reference effort? The system uses it but widens the confidence interval and warns about limited data.
- What happens when the user's best efforts are very old (>6 months)? The system still uses them but applies a recency discount and notes the age in output.
- What happens when the target distance is shorter than all available efforts? The system extrapolates down using the Riegel formula (which works bidirectionally) and notes it is a downward extrapolation.
- What happens when the user has no heart rate data? Readiness score omits HR-dependent components and recalculates using available components.
- What happens when there are fewer than 4 weeks of training data? Readiness score shows "insufficient training history" and only the raw Riegel prediction is displayed.
- What happens when the user specifies an unsupported distance string? The system shows supported distances and exits with an error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST predict race times using the Riegel formula: `T2 = T1 * (D2/D1)^1.06`, where T1 is a known effort time and D1/D2 are distances.
- **FR-002**: System MUST use the best available efforts from the last 6 months as reference points for prediction, preferring recent efforts.
- **FR-003**: System MUST support the following target distances: 1mi, 5K, 10K, half marathon (21.1K), and marathon (42.2K).
- **FR-004**: System MUST display a confidence interval around the predicted time, widening when data is sparse or old.
- **FR-005**: System MUST compute a readiness score (0-100) as a weighted composite of: training consistency (30%), volume trend (25%), taper status (25%), and PR recency (20%).
- **FR-006**: Training consistency component MUST measure the percentage of weeks with at least 3 activities over the last 8 weeks.
- **FR-007**: Volume trend component MUST compare the last 4 weeks of volume to the prior 4 weeks, scoring higher when volume is maintained or appropriately tapering.
- **FR-008**: Taper status component MUST detect whether volume has decreased over the last 2-3 weeks while intensity is maintained, indicating race readiness.
- **FR-009**: PR recency component MUST score higher when the user's best efforts at reference distances are more recent.
- **FR-010**: System MUST support a `--distance` flag accepting: `1mi`, `5K`, `10K`, `half`, `marathon`.
- **FR-011**: System MUST support an optional `--race-date` flag (format: YYYY-MM-DD) that adds temporal context (days until race, phase alignment).
- **FR-012**: System MUST support a `--type` flag (default: "Run") to filter activities by type.
- **FR-013**: System MUST produce valid JSON output when the global `--json` flag is active, containing all prediction and readiness data.
- **FR-014**: System MUST show an informative error when fewer than 2 reference efforts are available for prediction.
- **FR-015**: System MUST display reference efforts used for the prediction (distance, time, date) so users understand the basis.

### Key Entities

- **ReferenceEffort**: A user's best effort at a known distance — includes distance, elapsed time, pace, activity date, and activity ID. Used as input to the Riegel formula.
- **Prediction**: The computed race prediction — includes target distance, predicted time, predicted pace, confidence interval (low/high), and the reference efforts used.
- **ReadinessScore**: A composite fitness assessment — includes overall score (0-100) and component breakdown (consistency, volume trend, taper status, PR recency), each scored 0-100.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view a race prediction for any supported distance in under 5 seconds.
- **SC-002**: Predictions include a confidence range that narrows with more reference data (2 efforts = wide, 4+ efforts = narrow).
- **SC-003**: Readiness score provides 4 labeled components so users understand what is driving their score.
- **SC-004**: Users with race dates see days-until-race and training phase alignment in the output.
- **SC-005**: JSON output is parseable and contains all fields needed for an agent to build a race-day pacing strategy.
- **SC-006**: The system handles edge cases (insufficient data, old efforts, unsupported distances) with clear, actionable messages rather than errors.

## Assumptions

- The Riegel exponent of 1.06 is a well-established default for recreational runners. No user-configurable exponent is needed.
- "Best effort" at a distance is determined from the existing personal records scan (PR database from Feature 1.2) or computed on-the-fly from activity distance/time data.
- Reference efforts from the last 6 months are preferred; older efforts are usable but receive a recency discount in confidence calculations.
- The readiness score weights (30/25/25/20) are reasonable defaults based on coaching literature. They are not user-configurable.
- Heart rate data is optional — readiness components that need HR gracefully degrade when unavailable.
- Cycling predictions are out of scope for MVP (running only), though `--type` filter is supported for future extension.
