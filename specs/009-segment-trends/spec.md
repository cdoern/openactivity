# Feature Specification: Segment Trend Analysis

**Feature Branch**: `009-segment-trends`
**Created**: 2026-03-23
**Status**: Draft
**Input**: User description: "Show performance trends on repeated segments with linear regression, rate of change, and optional HR adjustment."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Segment Performance Trend (Priority: P1)

As a runner who regularly runs the same segments, I want to see whether I'm getting faster or slower on a specific segment over time, so I can track my fitness progression on familiar routes.

The user runs `openactivity strava segment <ID> trend` and sees a trend analysis: direction (improving/declining/stable), rate of change in seconds per month, best/worst/most recent effort, and the effort history.

**Why this priority**: This is the core value — answering "am I getting faster or slower?" on a segment. Without this, the feature has no purpose.

**Independent Test**: Run `openactivity strava segment <ID> trend` with a segment that has 3+ efforts and verify trend direction, rate of change, and effort summary are displayed.

**Acceptance Scenarios**:

1. **Given** the user has 3+ efforts on a segment, **When** they run `segment <ID> trend`, **Then** they see trend direction (improving/declining/stable), rate of change (seconds/month), best effort, worst effort, most recent effort, and total effort count.
2. **Given** the user has fewer than 3 efforts on a segment, **When** they run `segment <ID> trend`, **Then** they see the efforts listed but a message that more data is needed for trend analysis.
3. **Given** the segment ID does not exist in the local database, **When** they run `segment <ID> trend`, **Then** they see an informative error suggesting they sync segment data.

---

### User Story 2 - Segment List with Trend Indicators (Priority: P2)

As a runner reviewing my segments, I want to see trend indicators (improving/declining/stable) in the segments list, so I can quickly identify which segments I'm progressing on without checking each one individually.

The user runs `openactivity strava segments list` and sees a trend column alongside each segment.

**Why this priority**: Enhances the existing segments list with at-a-glance trend info, but the detailed trend command (US1) must work first.

**Independent Test**: Run `openactivity strava segments list` and verify a trend indicator column appears for segments with enough efforts.

**Acceptance Scenarios**:

1. **Given** the user has starred segments with 3+ efforts each, **When** they run `segments list`, **Then** each segment row includes a trend indicator (↑ improving, ↓ declining, → stable) and rate of change.
2. **Given** a segment has fewer than 3 efforts, **When** listed, **Then** the trend column shows "—" (insufficient data).

---

### User Story 3 - HR-Adjusted Trend (Priority: P3)

As an athlete who wants to understand effort-normalized performance, I want to see an HR-adjusted trend that accounts for how hard I was working, so I can distinguish between "I ran faster because I tried harder" and "I ran faster because I'm fitter."

The user runs `segment <ID> trend` and, when HR data is available, sees an additional HR-adjusted trend alongside the raw time trend.

**Why this priority**: Adds analytical depth but requires HR data which not all efforts have. The raw trend (US1) is valuable on its own.

**Independent Test**: Run `segment <ID> trend` on a segment where efforts have HR data and verify an HR-adjusted metric is shown.

**Acceptance Scenarios**:

1. **Given** a segment with 3+ efforts that all have HR data, **When** the user views the trend, **Then** they see both raw time trend and HR-adjusted trend (time normalized by average HR).
2. **Given** a segment where some efforts lack HR data, **When** the user views the trend, **Then** the HR-adjusted trend only uses efforts with HR data, noting the reduced sample size.
3. **Given** a segment with no HR data on any effort, **When** the user views the trend, **Then** only the raw time trend is shown with no HR section.

---

### User Story 4 - JSON Output (Priority: P4)

As an AI agent, I want structured JSON output from the segment trend command, so I can programmatically answer "Am I getting faster or slower on my regular Tuesday loop?"

**Why this priority**: Standard agent consumption pattern.

**Independent Test**: Run with `--json` flag and verify valid JSON.

**Acceptance Scenarios**:

1. **Given** the `--json` flag is active, **When** the user runs `segment <ID> trend`, **Then** the output is valid JSON containing trend direction, rate of change, effort history, and HR-adjusted data if available.

---

### Edge Cases

- What happens when a segment has exactly 1 effort? The system shows that single effort's details but states trend analysis requires at least 3 efforts.
- What happens when a segment has 2 efforts? The system shows both efforts and a simple comparison (faster/slower) but notes that 3+ efforts are needed for trend analysis.
- What happens when all efforts have the same time? The system reports "stable" trend with 0 seconds/month change.
- What happens when efforts span a very short period (e.g., all within 1 week)? The system computes the trend but warns that a short time span may not reflect long-term patterns.
- What happens when the segment ID is valid but has no efforts in the local DB? The system shows an error suggesting the user sync their data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute a linear regression of elapsed time vs date for all efforts on a segment to determine trend direction and rate.
- **FR-002**: System MUST classify the trend as "improving" (getting faster, negative slope), "declining" (getting slower, positive slope), or "stable" (slope within ±1 second/month).
- **FR-003**: System MUST report the rate of change in seconds per month.
- **FR-004**: System MUST display best effort (fastest time), worst effort (slowest time), and most recent effort with their dates.
- **FR-005**: System MUST require at least 3 efforts to compute a trend. With fewer efforts, show available data without trend analysis.
- **FR-006**: System MUST display all efforts in a chronological table showing date, elapsed time, average HR (if available), and delta from best.
- **FR-007**: System MUST support an HR-adjusted trend when HR data is available — normalize elapsed time by dividing by average HR, then compute regression on the normalized values.
- **FR-008**: System MUST extend the existing segments list to include a trend indicator column (↑/↓/→) and rate of change for segments with 3+ efforts.
- **FR-009**: System MUST produce valid JSON output when the global `--json` flag is active, containing all trend data, effort history, and HR-adjusted results.
- **FR-010**: System MUST show informative errors when the segment has no efforts or does not exist locally.

### Key Entities

- **SegmentTrend**: The computed trend for a segment — includes direction, rate of change (seconds/month), R-squared value, effort count, date range, and best/worst/recent efforts.
- **EffortSummary**: A single effort on a segment — includes date, elapsed time, average HR (optional), delta from best time, and HR-normalized time (optional).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view a segment trend analysis in under 3 seconds.
- **SC-002**: Trend direction accurately reflects the linear regression slope — improving when times decrease, declining when times increase.
- **SC-003**: The segments list displays trend indicators for all segments with 3+ efforts, giving at-a-glance fitness context.
- **SC-004**: HR-adjusted trends are shown alongside raw trends when HR data is available, enabling effort-normalized assessment.
- **SC-005**: JSON output contains all fields needed for an agent to answer "Am I getting faster or slower on this route?"
- **SC-006**: Edge cases (few efforts, no HR, unknown segment) produce clear, actionable messages.

## Assumptions

- Segment efforts are already synced and stored locally via `openactivity strava sync` — this feature reads from existing SegmentEffort data.
- The stable threshold is ±1 second/month — trends within this range are labeled "stable" to avoid over-interpreting noise.
- HR-adjusted normalization uses time/HR as the metric — lower values mean better performance at the same effort level.
- The `segment <ID> trend` command uses the segment's Strava numeric ID.
- Linear regression is sufficient for trend detection — polynomial or seasonal models are out of scope.
- The segments list enhancement only applies to starred segments (matching existing `segments list` behavior).
