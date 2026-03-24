# Feature Specification: Cross-Provider Activity Linking

**Feature Branch**: `011-cross-provider-linking`
**Created**: 2026-03-24
**Status**: Draft
**Input**: User description: "Cross-Provider Activity Linking: Automatically detect and link duplicate activities that exist in both Strava and Garmin."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bulk Link Existing Activities (Priority: P1)

A user has already synced Strava activities and imported Garmin FIT files. Many of these activities represent the same real-world workout recorded by both platforms. The user runs a single command to scan all unlinked activities and automatically create links between matching pairs. After linking, the unified activity list shows matched activities with a combined badge instead of duplicate entries.

**Why this priority**: This is the core value proposition — users with existing data from both providers need to deduplicate immediately. Without this, the activity list shows many duplicate entries.

**Independent Test**: Can be fully tested by importing activities from both providers and running the link command. Delivers immediate value by deduplicating the activity list.

**Acceptance Scenarios**:

1. **Given** a database with unlinked Strava and Garmin activities that overlap in time, **When** the user runs the link command, **Then** matching activities are linked and the output shows how many pairs were linked.
2. **Given** a database with activities that have already been linked, **When** the user runs the link command again, **Then** already-linked activities are skipped and only new matches are processed.
3. **Given** a database with activities from only one provider, **When** the user runs the link command, **Then** the system reports that no cross-provider matches were found.

---

### User Story 2 - Preview Matches Before Linking (Priority: P1)

A user wants to verify which activities will be linked before committing changes. They run the link command in dry-run mode to see all proposed matches with confidence scores, then decide whether to proceed.

**Why this priority**: Users need confidence that auto-matching is correct before bulk-modifying their data. Dry-run prevents irreversible mistakes.

**Independent Test**: Can be tested by running dry-run and verifying no database changes occur while matches are displayed.

**Acceptance Scenarios**:

1. **Given** a database with potential cross-provider matches, **When** the user runs the link command with dry-run enabled, **Then** proposed matches are displayed with confidence scores but no links are created.
2. **Given** the dry-run output shows a match the user disagrees with, **When** the user subsequently runs the actual link command, **Then** the system links all matches above the confidence threshold.

---

### User Story 3 - Auto-Link During Import and Sync (Priority: P2)

When a user imports new Garmin activities or syncs new Strava activities, newly added activities are automatically checked against the other provider's existing activities. Any matches are linked without requiring a separate manual step.

**Why this priority**: After the initial bulk link, ongoing linking should be seamless. Users shouldn't need to remember to run a separate command every time they import or sync.

**Independent Test**: Can be tested by syncing/importing new activities and verifying links are automatically created for matching activities.

**Acceptance Scenarios**:

1. **Given** existing Strava activities in the database, **When** the user imports Garmin FIT files that match some Strava activities, **Then** matching activities are automatically linked and the import summary includes linking stats.
2. **Given** existing Garmin activities in the database, **When** the user syncs Strava activities that match some Garmin activities, **Then** matching activities are automatically linked and the sync summary includes linking stats.
3. **Given** the user imports a Garmin activity with no Strava counterpart, **When** the import completes, **Then** no link is created and the activity appears normally as a Garmin-only entry.

---

### User Story 4 - Remove Incorrect Links (Priority: P3)

A user discovers that the system incorrectly linked two activities that are not actually the same workout. They can remove the link to restore them as separate activities.

**Why this priority**: Error correction is important but expected to be rare given the matching criteria. Lower priority than creating links.

**Independent Test**: Can be tested by creating a link, then unlinking it and verifying both activities appear separately again.

**Acceptance Scenarios**:

1. **Given** two activities that are incorrectly linked, **When** the user runs the unlink command with the activity ID, **Then** the link is removed and both activities appear as separate entries.
2. **Given** an activity that is not linked, **When** the user tries to unlink it, **Then** the system reports that no link exists for that activity.

---

### Edge Cases

- What happens when an activity matches multiple candidates from the other provider (e.g., two runs on the same day)? The system should link only the highest-confidence match and report ambiguous matches for manual review.
- What happens when activity types use different naming conventions across providers (e.g., Strava's `root='Run'` vs Garmin's `Run`, Strava's `root='AlpineSki'` vs Garmin's `Alpine_skiing`)? The fuzzy type matching must normalize these variations.
- What happens when a Garmin activity has no duration data? It should be skipped with a warning rather than causing a failure.
- What happens when the database has thousands of activities? The matching should complete within a reasonable time by only scanning unlinked activities and using time-based filtering to limit candidate comparisons.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a command to scan all unlinked activities and create links between matching cross-provider pairs based on start time (±60 seconds), activity type (fuzzy match), and duration (±5%).
- **FR-002**: System MUST support a dry-run mode that displays proposed matches with confidence scores without modifying the database.
- **FR-003**: System MUST automatically attempt to link newly imported/synced activities against the opposite provider's existing activities.
- **FR-004**: System MUST allow users to remove an incorrect link by specifying an activity ID.
- **FR-005**: System MUST display summary statistics after linking: total scanned, matches found, links created, already linked, skipped.
- **FR-006**: System MUST use a minimum confidence threshold of 0.7 (70%) for automatic linking; matches below this threshold are reported but not linked.
- **FR-007**: System MUST handle ambiguous matches (multiple candidates above threshold) by selecting the highest-confidence match and reporting the ambiguity.
- **FR-008**: System MUST normalize activity type names across providers before comparison (e.g., Strava's `root='Run'` matches Garmin's `Run`, Strava's `root='AlpineSki'` matches Garmin's `Alpine_skiing`).
- **FR-009**: The unified activity list MUST show linked activities with a combined provider badge (already implemented as `[Strava+Garmin]`).
- **FR-010**: System MUST designate a primary provider for each link (default: Strava, since it typically has richer metadata like GPS streams and segment efforts).

### Key Entities

- **ActivityLink**: A relationship between two activities from different providers representing the same real-world workout. Contains references to both the Strava and Garmin activity, a confidence score, and the designated primary provider.
- **Activity**: An existing entity that may belong to either provider. The `provider` field identifies the source and `provider_id` ensures uniqueness within a provider.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Bulk linking of several hundred activities completes in under 5 seconds.
- **SC-002**: At least 90% of true duplicate activities are correctly identified and linked.
- **SC-003**: Less than 1% of created links are false positives.
- **SC-004**: After linking, the unified activity list shows no visually obvious duplicates for activities recorded on both platforms.
- **SC-005**: Auto-linking during import/sync adds no more than 1 second of overhead per batch of new activities.
- **SC-006**: Dry-run output matches actual linking results when subsequently run without dry-run.

## Assumptions

- The existing `find_cross_provider_matches` function and the `activity_links` table schema are correct and sufficient — no schema migration is needed.
- The existing `_types_match` function handles the known type variations between providers. It may need extension for newly discovered type mismatches (e.g., `root='AlpineSki'` vs `Alpine_skiing`).
- Strava is the default primary provider for linked activities because it typically contains richer metadata (GPS streams, segment efforts, social data).
- The confidence threshold of 0.7 is appropriate for automatic linking. This can be adjusted based on real-world results.
- Activity start times from both providers are in UTC or consistently comparable timestamps.
