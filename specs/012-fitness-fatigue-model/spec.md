# Feature Specification: Fitness/Fatigue Model (ATL/CTL/TSB)

**Feature Branch**: `012-fitness-fatigue-model`
**Created**: 2026-03-24
**Status**: Draft
**Input**: User description: "Fitness/Fatigue Model — compute TSS, ATL, CTL, TSB from heart rate data across both providers."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Current Fitness, Fatigue, and Form (Priority: P1)

A runner or cyclist wants to understand their current training state: Are they fit? Fatigued? Peaking? The user runs a single command to see today's fitness (CTL), fatigue (ATL), and form (TSB) values along with a plain-language status label like "peaking" or "overreaching". This replaces what Strava Summit ($60/yr) and TrainingPeaks charge for.

**Why this priority**: This is the core value — a single command that tells the user "you are fit and fresh" or "you are fatigued, ease up". Everything else builds on this.

**Independent Test**: Run `openactivity analyze fitness` with 6+ months of activity data containing heart rate. Verify it shows CTL, ATL, TSB values and a status label.

**Acceptance Scenarios**:

1. **Given** a database with 6 months of activities with heart rate data, **When** the user runs the fitness command, **Then** the output shows today's CTL (fitness), ATL (fatigue), TSB (form), and a status label.
2. **Given** a database with activities from both Strava and Garmin (some linked), **When** the user runs the fitness command, **Then** linked activities are counted only once (not double-counted).
3. **Given** a database with no heart rate data on any activities, **When** the user runs the fitness command, **Then** the system shows a clear error explaining HR data is required.

---

### User Story 2 - View Fitness Trend Over Time (Priority: P1)

A user wants to see how their fitness, fatigue, and form have changed over a time range (e.g., last 6 months). They want a daily breakdown showing the trajectory — are they building fitness? Recovering? Stagnating?

**Why this priority**: The trend is as valuable as the current snapshot. Users need to see if they're improving or declining over weeks/months.

**Independent Test**: Run `openactivity analyze fitness --last 6m` and verify it shows a time-series of daily CTL/ATL/TSB values with trend direction.

**Acceptance Scenarios**:

1. **Given** activities spanning 6 months, **When** the user requests the last 6 months, **Then** the output shows daily fitness/fatigue/form values with overall trend direction (improving/declining/stable).
2. **Given** the `--type Run` filter, **When** the user runs the fitness command, **Then** only running activities contribute to the TSS calculations.
3. **Given** the `--json` flag, **When** the user runs the fitness command, **Then** the output is a JSON array of daily values with all fields.

---

### User Story 3 - Visualize Fitness Chart (Priority: P2)

A user wants to see their fitness/fatigue/form as a visual chart over time, similar to what TrainingPeaks shows. The chart plots CTL, ATL, and TSB on the same timeline so the user can visually identify peaks, recovery periods, and training blocks.

**Why this priority**: Visual representation makes patterns much easier to spot than a table of numbers. But the data computation (US1/US2) must work first.

**Independent Test**: Run `openactivity analyze fitness --last 6m --chart` and verify it generates a chart file showing three plotted lines.

**Acceptance Scenarios**:

1. **Given** 6 months of activity data, **When** the user requests a chart, **Then** a chart image is generated showing CTL, ATL, and TSB lines over time.
2. **Given** a chart request with `--output fitness.png`, **When** the command completes, **Then** the chart is saved to the specified path.

---

### User Story 4 - Per-Activity Training Stress Score (Priority: P2)

A user wants to see the Training Stress Score (TSS) for individual activities to understand which workouts contribute most to their training load. The TSS value should appear in the activity detail view.

**Why this priority**: Adds granularity — users can identify their hardest workouts and understand how each session affects their overall load.

**Independent Test**: Run `openactivity activity <ID>` for an activity with HR data and verify a TSS value is shown.

**Acceptance Scenarios**:

1. **Given** an activity with heart rate data, **When** the user views activity detail, **Then** the TSS value is displayed alongside other metrics.
2. **Given** an activity without heart rate data, **When** the user views activity detail, **Then** no TSS is shown (gracefully omitted, not an error).

---

### Edge Cases

- What happens when an activity has average HR but no HR stream? Use average HR with a simplified TRIMP estimate rather than requiring per-second stream data.
- What happens when the user has only 1 week of data? Show values but warn that CTL (42-day window) is not yet reliable.
- What happens when there are multi-day gaps (e.g., rest weeks, injury)? TSS is 0 for rest days; ATL/CTL decay naturally via the exponential formula.
- What happens when linked activities exist? Use only the primary provider's data (Strava by default) to avoid double-counting.
- What happens when the user's max heart rate is unknown? Estimate from age (220 - age) or from the highest HR observed across all activities.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute a Training Stress Score (TSS) for each activity that has heart rate data, using a TRIMP-based formula that accounts for exercise duration and heart rate intensity relative to the user's maximum heart rate.
- **FR-002**: System MUST compute daily Acute Training Load (ATL) as an exponentially weighted rolling average of daily TSS with a 7-day time constant.
- **FR-003**: System MUST compute daily Chronic Training Load (CTL) as an exponentially weighted rolling average of daily TSS with a 42-day time constant.
- **FR-004**: System MUST compute daily Training Stress Balance (TSB) as CTL minus ATL.
- **FR-005**: System MUST classify the user's current training state based on TSB and CTL trends into one of: peaking (high CTL + positive TSB), maintaining (stable CTL + near-zero TSB), overreaching (rising CTL + very negative TSB), or detraining (declining CTL + positive TSB).
- **FR-006**: System MUST support time range filters: `--last` with values like `30d`, `90d`, `6m`, `1y`, `all`.
- **FR-007**: System MUST support activity type filter: `--type Run|Ride|Swim` to compute load for a specific discipline.
- **FR-008**: System MUST use data from both Strava and Garmin providers, deduplicating linked activities (using only the primary provider's data for linked pairs).
- **FR-009**: System MUST support `--json` output returning daily values and current status for programmatic consumption.
- **FR-010**: System MUST support `--chart` to generate a visual chart of CTL/ATL/TSB over the selected time range.
- **FR-011**: System MUST handle activities without heart rate data gracefully by skipping them (not failing) and reporting how many activities were excluded.
- **FR-012**: System MUST estimate max heart rate from the highest observed HR across all activities when the user has not configured a manual value.
- **FR-013**: System MUST display per-activity TSS in the activity detail view for activities that have heart rate data.

### Key Entities

- **Training Stress Score (TSS)**: A per-activity measure of training load computed from heart rate intensity and duration. Ranges from ~20 (easy 30-min jog) to ~300+ (marathon race effort).
- **Acute Training Load (ATL)**: 7-day exponentially weighted average of daily TSS. Represents short-term fatigue. Higher = more fatigued.
- **Chronic Training Load (CTL)**: 42-day exponentially weighted average of daily TSS. Represents long-term fitness. Higher = more fit.
- **Training Stress Balance (TSB)**: CTL minus ATL. Positive = fresh/recovered. Negative = fatigued. The "form" metric.
- **Training Status**: A classification derived from TSB and CTL trends — peaking, maintaining, overreaching, or detraining.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Fitness command returns results in under 2 seconds for 1 year of activity data (~365 days, ~200 activities).
- **SC-002**: TSS values for well-known activity profiles (easy run, tempo run, race) fall within accepted ranges per sports science literature (e.g., easy 30-min run ~30-50 TSS, hard 60-min tempo ~80-120 TSS).
- **SC-003**: CTL/ATL/TSB values match hand-calculated results for a test dataset within 1% tolerance.
- **SC-004**: Status labels correctly classify at least 4 distinct training states when given synthetic activity patterns (build phase, taper, recovery, detraining).
- **SC-005**: Users with data from both providers see consistent results whether they filter by provider or use the combined view.
- **SC-006**: Chart generation completes in under 5 seconds and produces a readable image with three distinct lines.

## Assumptions

- Max heart rate estimation using the highest observed HR is an acceptable default. Users can override this with a manually configured value in the future (out of scope for this feature).
- The TRIMP (Training Impulse) method is used for TSS calculation rather than power-based TSS, since HR data is universally available across both providers while power data is not.
- Activities without HR data contribute 0 TSS and are simply skipped in the load model.
- The standard time constants of 7 days (ATL) and 42 days (CTL) are used, matching industry-standard implementations (TrainingPeaks, Strava Summit).
- Rest days (no activity) contribute 0 TSS, causing ATL to decay faster than CTL, which is the correct behavior for modeling recovery.
- For linked Strava+Garmin activities, the Strava activity's data is used (as it is the primary provider with richer metadata).
- The existing `matplotlib` dependency (already in the project for charts) will be used for chart generation.
