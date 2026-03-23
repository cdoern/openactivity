# Feature Specification: Training Block / Periodization Detector

**Feature Branch**: `006-training-periodization`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Automatically detect training phases (base, build, peak, recovery) from volume and intensity patterns over time. Help users understand where they are in their training cycle without manual logging."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Training Block Timeline (Priority: P1)

A runner wants to understand their training history at a glance without manually logging phases. They run a command and see a timeline of detected training blocks (base, build, peak, recovery) with date ranges, showing how their training has been structured over the past several months. This answers: "What phase was I in last month, and what am I in now?"

**Why this priority**: The block timeline is the core value — it transforms raw activity data into meaningful training phase awareness. Everything else builds on this.

**Independent Test**: Can be tested by running the blocks command and verifying a chronological list of detected training phases with date ranges, classifications, and summary metrics.

**Acceptance Scenarios**:

1. **Given** a user with 6+ months of running activities, **When** they run the blocks command, **Then** they see a timeline of training blocks with date ranges, phase classification (base/build/peak/recovery), and summary metrics per block.
2. **Given** a user with consistent high-volume, low-intensity training for several weeks, **When** they view the timeline, **Then** those weeks are grouped into a "Base" block.
3. **Given** a user with rising volume and intensity over several weeks, **When** they view the timeline, **Then** those weeks are grouped into a "Build" block.
4. **Given** a user with fewer than 4 weeks of activity data, **When** they run the command, **Then** they see a message explaining that more data is needed for block detection.

---

### User Story 2 - Filter by Time Window and Activity Type (Priority: P2)

A runner or cyclist wants to analyze periodization for a specific sport and time range. They filter by activity type (Run or Ride) and time window (6 months, 1 year, or all time) to focus on relevant training blocks.

**Why this priority**: Filtering is essential for multi-sport athletes and for focusing on relevant training periods, but the core detection must work first.

**Independent Test**: Can be tested by running the blocks command with different `--last` and `--type` flags and verifying that results change appropriately.

**Acceptance Scenarios**:

1. **Given** a user with both running and cycling activities, **When** they filter by `--type Run`, **Then** only running activities contribute to block detection.
2. **Given** a user who specifies `--last 6m`, **Then** only the last 6 months of data are analyzed.
3. **Given** a user who specifies `--last all`, **Then** all available activity data is analyzed.

---

### User Story 3 - Current Phase Identification (Priority: P3)

A runner wants a quick answer to "Where am I right now in my training?" The output highlights the current (most recent) training phase and provides context about what it means — whether they should be pushing harder, maintaining, or recovering.

**Why this priority**: Identifying the current phase is the most actionable output, but it depends on the detection algorithm (US1) being solid first.

**Independent Test**: Can be tested by verifying the output includes a distinct "current phase" indicator with the most recent block highlighted and contextual guidance.

**Acceptance Scenarios**:

1. **Given** a user in a recovery phase, **When** they view the blocks output, **Then** the current block is clearly marked and the classification reads "Recovery."
2. **Given** a user whose most recent weeks show rising volume and intensity, **When** they view the output, **Then** the current phase shows "Build" with context about the trend.

---

### User Story 4 - JSON Output for Agent Consumption (Priority: P4)

An AI agent or script wants to programmatically query the user's current training phase and block history. The command supports structured JSON output so agents can answer questions like "Am I in a build phase or should I be recovering?"

**Why this priority**: JSON output enables agent-first use cases but depends on the core detection and display being complete.

**Independent Test**: Can be tested by running the blocks command with the JSON flag and verifying valid, parseable JSON output with all block data.

**Acceptance Scenarios**:

1. **Given** a user running the blocks command with JSON output, **When** blocks are detected, **Then** the output is valid JSON containing all blocks with phase, date ranges, and metrics.
2. **Given** an agent querying the current phase, **When** the JSON output is parsed, **Then** the current block is identifiable by its position (most recent) and a `current` flag.

---

### Edge Cases

- What happens when the user has fewer than 4 weeks of data? Display a message that at least 4 weeks of activity data are needed for meaningful block detection.
- What happens when the user has large gaps (>2 weeks) between activities? Treat the gap as a break — end the current block and start a new one after the gap.
- What happens when a week has zero activities? Count it as a recovery week with zero volume.
- What happens when all weeks look similar (no variation in volume/intensity)? Classify the entire period as "Base" (steady-state training).
- What happens with very short activities (<10 minutes)? Include them in volume calculations but note they have minimal impact.
- What happens when HR data is unavailable for some activities? Use pace-based intensity for those activities; if neither HR nor pace is available, use volume only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute weekly training volume (total distance and total duration) for each week in the analysis window.
- **FR-002**: System MUST compute weekly training intensity using average heart rate when available, falling back to average pace relative to the user's pace distribution.
- **FR-003**: System MUST classify each week into one of four phases: recovery, base, build, or peak.
- **FR-004**: System MUST group consecutive weeks with the same classification into named training blocks with start and end dates.
- **FR-005**: System MUST support time window filtering via `--last` flag accepting "6m", "1y", or "all" (default: "6m").
- **FR-006**: System MUST support activity type filtering via `--type` flag (default: "Run").
- **FR-007**: System MUST display the current (most recent) training phase with a visual indicator.
- **FR-008**: System MUST show per-block summary metrics: total distance, activity count, average weekly volume, and average intensity.
- **FR-009**: System MUST support structured JSON output with all block data when the JSON flag is used.
- **FR-010**: System MUST handle gaps in training data (>2 weeks with no activities) by ending the current block and starting fresh.
- **FR-011**: System MUST require at least 4 weeks of activity data; display an informative message if insufficient data exists.
- **FR-012**: System MUST classify weeks using a 4-week rolling average as the baseline for volume comparisons.

### Key Entities

- **WeekSummary**: A single week's aggregated training data. Attributes: week start date, total distance, total duration, activity count, average intensity (HR-based or pace-based), intensity source (HR or pace).
- **TrainingBlock**: A consecutive group of weeks sharing the same phase classification. Attributes: phase (base/build/peak/recovery), start date, end date, week count, total distance, activity count, average weekly volume, average intensity, whether it is the current block.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Block detection for 6 months of data (26 weeks) completes within 3 seconds.
- **SC-002**: Block detection for 1 year of data (52 weeks) completes within 5 seconds.
- **SC-003**: Recovery weeks are correctly identified when weekly volume drops below 70% of the 4-week rolling average.
- **SC-004**: All commands produce valid, parseable JSON when the JSON flag is used.
- **SC-005**: Users with fewer than 4 weeks of data see a clear message rather than empty or confusing output.
- **SC-006**: Block classifications are consistent — the same data always produces the same blocks.

## Assumptions

- Weekly boundaries are Monday through Sunday, aligned with ISO week numbering.
- Intensity is computed as a normalized score (0-100) where higher means more intense. When HR is available, intensity is the average HR across the week's activities as a percentage of estimated max HR. When HR is unavailable, intensity is derived from pace relative to the user's pace distribution (faster relative pace = higher intensity).
- Classification thresholds:
  - **Recovery**: Weekly volume < 70% of 4-week rolling average volume.
  - **Base**: Weekly volume >= 70% of rolling average AND intensity score < 60.
  - **Build**: Weekly volume >= 70% of rolling average AND intensity score >= 60 AND volume is rising (current week > previous week's rolling average).
  - **Peak**: Intensity score >= 70 AND volume is tapering (current week volume < previous week volume for 2+ consecutive weeks).
- When neither HR nor pace data is available for a week, intensity defaults to 50 (neutral).
- The 4-week rolling average requires at least 4 weeks of data; weeks before the 4th are classified based on absolute thresholds.
- Gaps of more than 14 consecutive days with no activities force a block boundary.
