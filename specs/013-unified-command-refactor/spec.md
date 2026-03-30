# Feature Specification: Unified Command Refactoring

**Feature Branch**: `013-unified-command-refactor`
**Created**: 2026-03-29
**Status**: Draft
**Input**: Refactor remaining Strava-specific commands to be provider-agnostic at the root level.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Analysis Commands Without Provider Prefix (Priority: P1)

A user who has imported activities from both Strava and Garmin wants to analyze their training data. They run `openactivity analyze pace` and get results combining activities from all providers. They no longer need to remember which commands live under `strava` vs the root.

**Why this priority**: This is the core value — users shouldn't need to think about providers when analyzing their own data. The `analyze` subgroup has the most subcommands and is the most frequently used.

**Independent Test**: Run `openactivity analyze pace` with both Strava and Garmin activities in the DB and verify results include data from both providers.

**Acceptance Scenarios**:

1. **Given** a user has activities from Strava and Garmin, **When** they run `openactivity analyze pace`, **Then** the output includes activities from both providers.
2. **Given** a user runs `openactivity analyze pace --provider garmin`, **When** results are returned, **Then** only Garmin activities are included.
3. **Given** a user runs `openactivity strava analyze pace`, **When** results are returned, **Then** the command still works (backwards compatibility) and behaves identically to `openactivity analyze pace --provider strava`.

---

### User Story 2 - View Personal Records Across All Providers (Priority: P1)

A user wants to see their PRs regardless of whether the activity was recorded via Strava or Garmin. They run `openactivity records list` and see PRs detected from activities across all providers.

**Why this priority**: PRs are a key feature and should reflect the user's best performances regardless of which device/service recorded them.

**Independent Test**: Run `openactivity records scan` then `openactivity records list` and verify PRs are found from both Strava and Garmin activities.

**Acceptance Scenarios**:

1. **Given** a user has running activities from both providers, **When** they run `openactivity records scan`, **Then** activities from all providers are scanned for PRs.
2. **Given** a user runs `openactivity records list`, **When** results display, **Then** PRs from any provider are shown.
3. **Given** a user runs `openactivity strava records list`, **When** results display, **Then** the command still works for backwards compatibility.

---

### User Story 3 - Predict Race Times Using All Available Data (Priority: P2)

A user wants race predictions based on their best recent training data, regardless of provider. They run `openactivity predict --distance half` and get predictions informed by the best available data from any provider.

**Why this priority**: Predictions improve with more data. Limiting to one provider produces worse results.

**Independent Test**: Run `openactivity predict --distance 5K` and verify it considers activities from all providers.

**Acceptance Scenarios**:

1. **Given** a user has activities from multiple providers, **When** they run `openactivity predict --distance 10K`, **Then** predictions use best efforts from any provider.
2. **Given** a user runs `openactivity strava predict --distance 10K`, **When** results display, **Then** the command still works for backwards compatibility.

---

### User Story 4 - Browse Segments at Top Level (Priority: P2)

A user wants to view their segment performances. They run `openactivity segments list` instead of `openactivity strava segments list`.

**Why this priority**: Segments exist in Garmin data too. Promoting to top-level sets up future multi-provider segment support.

**Independent Test**: Run `openactivity segments list` and verify it returns segment data.

**Acceptance Scenarios**:

1. **Given** a user has segment data, **When** they run `openactivity segments list`, **Then** segments are displayed.
2. **Given** a user runs `openactivity segment <ID>`, **When** results display, **Then** segment detail is shown.
3. **Given** a user runs `openactivity strava segments list`, **When** results display, **Then** the command still works for backwards compatibility.

---

### User Story 5 - Provider-Specific Commands Stay Namespaced (Priority: P1)

Provider-specific operations like authentication and syncing remain under their provider namespace. A user runs `openactivity strava auth` to authenticate with Strava and `openactivity garmin import` to import from Garmin. These do not move to the root level.

**Why this priority**: Auth, sync, and import are inherently provider-specific and moving them would be confusing.

**Independent Test**: Run `openactivity strava auth` and `openactivity garmin import --help` and verify they work under their provider namespaces.

**Acceptance Scenarios**:

1. **Given** a user wants to authenticate with Strava, **When** they run `openactivity strava auth`, **Then** the OAuth flow starts.
2. **Given** a user wants to import Garmin data, **When** they run `openactivity garmin import --from-device`, **Then** the import runs.
3. **Given** a user runs `openactivity strava sync`, **When** the sync completes, **Then** data is synced from Strava.

---

### Edge Cases

- What happens when a user runs a deprecated `openactivity strava analyze` path? It still works identically for backwards compatibility.
- What happens when `--provider` is set to a provider that has no activities? The command returns an empty result set with an informative message.
- What happens when the `strava athlete` command is run? It stays under `strava` since it is Strava-specific.
- What happens when a user has only one provider's data? All commands work normally, just with that provider's data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `analyze` command group (pace, blocks, effort, fitness, correlate, compare) MUST be available at the root level (`openactivity analyze ...`).
- **FR-002**: The `records` command group (scan, list, history, add-distance, remove-distance) MUST be available at the root level (`openactivity records ...`).
- **FR-003**: The `predict` command MUST be available at the root level (`openactivity predict ...`).
- **FR-004**: The `segments` and `segment` commands MUST be available at the root level (`openactivity segments ...`, `openactivity segment ...`).
- **FR-005**: All promoted commands MUST accept an optional `--provider` flag to filter results to a single provider (e.g., `--provider garmin`, `--provider strava`).
- **FR-006**: When no `--provider` flag is specified, promoted commands MUST include data from all providers.
- **FR-007**: The `strava analyze`, `strava records`, `strava predict`, `strava segments`, and `strava segment` commands MUST continue to work for backwards compatibility, behaving as aliases to the top-level versions filtered to Strava data.
- **FR-008**: Provider-specific commands (`strava auth`, `strava sync`, `strava athlete`, `garmin import`) MUST remain under their provider namespaces and NOT be promoted.
- **FR-009**: The duplicate `strava activities` and `strava activity` commands MUST be removed or aliased to the existing top-level `activities` and `activity` commands.
- **FR-010**: The `--provider` filter MUST be consistent across all promoted commands (same flag name, same accepted values).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All analysis, records, predict, and segment commands are accessible from the root level without a provider prefix.
- **SC-002**: Running any promoted command without `--provider` returns results from all providers in the database.
- **SC-003**: Running any promoted command with `--provider strava` returns only Strava results.
- **SC-004**: All previously-working `openactivity strava ...` command paths continue to function without errors.
- **SC-005**: Provider-specific commands (`auth`, `sync`, `import`, `athlete`) are only accessible under their provider namespace.
- **SC-006**: The `openactivity --help` output shows the promoted commands at the root level with clear descriptions.

## Assumptions

- The top-level `analyze` command group already exists with the `fitness` subcommand; this refactoring extends it with the remaining subcommands.
- Backwards compatibility is achieved by keeping the `strava` subcommands as aliases that implicitly pass `--provider strava`, not by maintaining duplicate code.
- No database schema changes are required for this refactoring.
- The `strava athlete` command is inherently Strava-specific and stays under `strava`.
