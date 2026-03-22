# Feature Specification: Personal Records Database

**Feature Branch**: `004-personal-records`
**Created**: 2026-03-21
**Status**: Draft
**Input**: User description: "Automatically detect and track PRs across standard distances and power durations by scanning activity streams. Show current PRs, PR progression history, support custom distances, and persist records for instant lookup. Strava only tracks a handful of preset distances and doesn't show PR progression over time."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scan Activities and View Current PRs (Priority: P1)

A user wants to know their personal best times across standard running distances and best power outputs for cycling. They run a scan command that analyzes their synced activity data and detects the fastest effort for each standard distance (1mi, 5K, 10K, half marathon, marathon) and best average power for key durations (5s, 1min, 5min, 20min, 60min). They then view their current PRs in a table showing the distance/duration, best time or power, pace/watts, the date it was set, and which activity it came from.

**Why this priority**: This is the core value — without scanning and storing PRs, no other feature works. Viewing current PRs is the most common use case.

**Independent Test**: Can be tested by syncing activities with distance/time stream data, running the scan command, then running the list command and verifying that the correct best efforts appear for each standard distance.

**Acceptance Scenarios**:

1. **Given** a user with synced running activities containing distance and time streams, **When** they run the scan command, **Then** the system detects the best effort for each standard running distance and persists the records.
2. **Given** a user with synced cycling activities containing power streams, **When** they run the scan command, **Then** the system detects the best average power for each standard duration and persists the records.
3. **Given** a user who has scanned their activities, **When** they run the list command, **Then** they see a table of their current PRs organized by category (running distances, cycling power).
4. **Given** a user with no activities matching a particular distance, **When** they view their PRs, **Then** that distance shows as "—" (no record) rather than erroring.
5. **Given** a user who runs the scan command again after syncing new activities, **When** a new activity contains a faster effort, **Then** the PR is updated and the previous record is preserved in history.

---

### User Story 2 - View PR Progression History (Priority: P2)

A user wants to see how their PR for a specific distance has improved over time. They run a history command for a distance (e.g., 5K) and see a chronological list of every time they set a new PR, showing the progression from their first record to their current best.

**Why this priority**: PR progression is the key differentiator over Strava — it shows fitness improvement over time, not just the current best.

**Independent Test**: Can be tested by scanning activities that contain multiple improving efforts at a specific distance, then viewing the history for that distance and verifying the chronological progression is correct.

**Acceptance Scenarios**:

1. **Given** a user with multiple PRs set over time for 5K, **When** they run the history command for 5K, **Then** they see a chronological list showing each PR with date, time, pace, improvement delta, and activity name.
2. **Given** a user requesting history for a distance with no records, **When** they run the history command, **Then** they see a message indicating no records exist for that distance.
3. **Given** a user requesting history with the JSON flag, **When** the command completes, **Then** the output is valid JSON with the full progression data.

---

### User Story 3 - Add Custom Distances (Priority: P3)

A user trains for non-standard race distances (e.g., 15K, 25K, 50K) and wants to track PRs for those distances too. They add a custom distance, then re-scan to detect best efforts at that distance.

**Why this priority**: Custom distances extend the feature to ultrarunners, triathletes, and users with non-standard training targets. It depends on the core scanning infrastructure from US1.

**Independent Test**: Can be tested by adding a custom distance, running the scan command, and verifying that the custom distance appears in the PR list with correct best effort data.

**Acceptance Scenarios**:

1. **Given** a user who wants to track 15K PRs, **When** they run the add-distance command with "15K", **Then** the distance is registered and available for scanning.
2. **Given** a user who has added a custom distance, **When** they run the scan command, **Then** best efforts are detected for the custom distance alongside standard distances.
3. **Given** a user who tries to add a distance that already exists (e.g., "5K"), **When** they run the add-distance command, **Then** they see a message that the distance already exists.
4. **Given** a user who wants to remove a custom distance, **When** they run a remove-distance command, **Then** the distance and its records are removed.

---

### User Story 4 - JSON Output for Agent Consumption (Priority: P4)

An AI agent or script wants to programmatically query PR data. All record commands support structured JSON output so agents can answer questions like "What's my 5K PR and when did I set it?" or "How has my marathon time improved?"

**Why this priority**: JSON output enables the agent-first use case. It depends on the data being available from US1/US2.

**Independent Test**: Can be tested by running any records command with the JSON flag and verifying valid, parseable JSON output.

**Acceptance Scenarios**:

1. **Given** a user running the list command with JSON output, **When** the command completes, **Then** the output is valid JSON containing all PR records with distances, times, paces, dates, and activity references.
2. **Given** a user running the history command with JSON output for a specific distance, **When** the command completes, **Then** the output includes the full progression array with deltas between records.

---

### Edge Cases

- What happens when an activity's distance stream doesn't cover the full target distance? Only distances fully contained within the activity should be eligible for PR detection.
- What happens when a user has only one effort at a distance? It should still be recorded as the PR (there's no "improvement" to show, but it's still their best).
- What happens with treadmill or indoor activities that lack GPS data but have distance? They should still be scanned since distance/time data is available.
- What happens when scanning detects the same time for two different activities at the same distance? The earlier activity should be treated as the original PR.
- What happens with very short activities (e.g., 200m)? Standard distances shorter than the activity's total distance should still be scanned using the sliding window.
- How does the system handle activities with paused segments? Moving time (not elapsed time) should be used for PR detection.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support scanning activity distance and time stream data to detect best efforts at standard running distances: 1 mile, 5K, 10K, half marathon (21.0975 km), and marathon (42.195 km).
- **FR-002**: System MUST support scanning activity power stream data to detect best average power for standard cycling durations: 5 seconds, 1 minute, 5 minutes, 20 minutes, and 60 minutes.
- **FR-003**: System MUST persist detected personal records with the distance or duration type, achieved time or power, pace or watts, the source activity reference, and the date achieved.
- **FR-004**: System MUST preserve previous PR records when a new PR is set, maintaining a full history chain for each distance/duration.
- **FR-005**: System MUST display current PRs in a formatted table organized by category (running distances, cycling power durations).
- **FR-006**: System MUST display PR progression history for a specific distance/duration showing chronological improvements with deltas between records.
- **FR-007**: System MUST support adding custom distances for PR tracking beyond the built-in standard set.
- **FR-008**: System MUST support removing custom distances and their associated records.
- **FR-009**: System MUST use a sliding window algorithm over distance/time streams to find the fastest segment matching each target distance within an activity.
- **FR-010**: System MUST use moving time (not elapsed time) for PR calculations to exclude paused segments.
- **FR-011**: System MUST only consider efforts where the activity's distance stream fully covers the target distance.
- **FR-012**: System MUST support structured JSON output on all records commands for programmatic consumption.
- **FR-013**: System MUST support incremental scanning — when re-scanning, only process activities not previously scanned rather than re-processing all activities.
- **FR-014**: System MUST respect the user's configured unit system when displaying distances and paces.

### Key Entities

- **PersonalRecord**: A best effort at a specific distance or power duration. Attributes: distance/duration type identifier, achieved time (seconds) or power (watts), pace or speed, source activity reference, date achieved, whether it is the current record or a superseded historical record.
- **CustomDistance**: A user-defined distance for PR tracking beyond the built-in standard set. Attributes: distance label (e.g., "15K"), distance in meters.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Scanning 1,000 activities completes within 30 seconds.
- **SC-002**: Listing current PRs returns results within 1 second.
- **SC-003**: PR history for any distance returns results within 1 second.
- **SC-004**: All standard running distances (1mi, 5K, 10K, half, marathon) and cycling power durations (5s, 1m, 5m, 20m, 60m) are detected when matching activity data exists.
- **SC-005**: PR progression accurately shows every improvement in chronological order with correct time deltas.
- **SC-006**: JSON output is valid and parseable, containing all data present in table views.
- **SC-007**: Custom distances are scannable and appear in PR listings alongside standard distances.
- **SC-008**: Re-scanning after new activities only processes unscanned activities, completing proportionally faster.

## Clarifications

### Session 2026-03-21

- Q: Should PR scanning run automatically after every sync, or only when the user explicitly runs the scan command? → A: Manual scan only (user runs scan command explicitly).

## Assumptions

- Distance streams contain cumulative distance data in meters with corresponding time data, which is the standard format from Strava's activity streams.
- Power streams contain instantaneous watts readings at regular intervals (typically 1-second resolution).
- The sliding window for distance-based PRs uses the distance stream to find start/end indices where the cumulative distance delta matches the target distance, then computes elapsed moving time between those indices.
- Standard distances are pre-configured and cannot be removed (only custom distances can be added/removed).
- PR scanning is manual only — users must explicitly run the scan command. It does not run automatically during sync.
- When multiple activities contain the same best time for a distance, the earliest activity chronologically is treated as the original PR holder.
