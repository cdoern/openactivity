# Feature Specification: OpenActivity Strava CLI

**Feature Branch**: `001-strava-cli`
**Created**: 2026-03-13
**Status**: Draft
**Input**: User description: "Create a CLI tool called openactivity which connects to the Strava API. `openactivity strava` is the parent command group. The CLI should expose useful tooling for pulling data from Strava, presenting it, exporting it in graphs, tables, etc. The CLI should be intuitive for humans and agents to use. The goal is to extrapolate more data in a useful way than what sites like Strava show their users."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Authenticate with Strava (Priority: P1)

A user installs openactivity and wants to connect their Strava account. They run an authentication command that walks them through authorizing the app. Once complete, their credentials are stored securely and all subsequent commands work without re-authenticating. Tokens refresh automatically when expired.

**Why this priority**: Nothing works without authentication. This is the gateway to all other functionality.

**Independent Test**: Can be fully tested by running the auth command, completing the OAuth flow, and verifying that a subsequent command (e.g., listing activities) succeeds without re-prompting for credentials.

**Acceptance Scenarios**:

1. **Given** a user with no stored credentials, **When** they run `openactivity strava auth`, **Then** they are guided through the OAuth authorization flow and credentials are stored securely.
2. **Given** a user with an expired access token, **When** they run any Strava command, **Then** the token is automatically refreshed without user intervention.
3. **Given** a user who wants to disconnect, **When** they run `openactivity strava auth revoke`, **Then** stored credentials are deleted and the user is informed.
4. **Given** a user running auth for the first time, **When** they have not configured their Strava API credentials, **Then** the CLI guides them through providing their client ID and client secret, with clear instructions on how to register a Strava API application at the developer portal.
5. **Given** a user with stored client credentials, **When** they run `openactivity strava auth`, **Then** the OAuth flow uses their registered app and does not prompt for client ID/secret again.

---

### User Story 2 - Browse and Search Activities (Priority: P2)

A user wants to see their Strava activities from the command line. After running `openactivity strava sync` to pull data into local storage, they can list activities, filter by date range, activity type (run, ride, swim, etc.), and search by name. Output is a readable table by default, with `--json` available for programmatic use. They can also view detailed information about a specific activity including splits, laps, and zone distributions. All list and detail commands query local data — no network calls required.

**Why this priority**: Viewing activity data is the core value proposition. Without the ability to list and inspect activities, export and analysis features have nothing to work with.

**Independent Test**: Can be tested by authenticating, then listing activities and verifying the output contains expected fields (name, date, distance, duration, type). Viewing a specific activity by ID should show detailed data.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they run `openactivity strava activities list`, **Then** they see a table of their recent activities showing name, date, type, distance, duration, and elevation.
2. **Given** an authenticated user, **When** they run `openactivity strava activities list --type run --after 2026-01-01`, **Then** only running activities from 2026 onward are shown.
3. **Given** an authenticated user, **When** they run `openactivity strava activity <ID>`, **Then** they see detailed information including splits, laps, heart rate zones, pace/power zones, and gear used.
4. **Given** an authenticated user, **When** they run `openactivity strava activities list --json`, **Then** output is valid JSON suitable for piping to other tools or agent consumption.
5. **Given** an authenticated user with no activities matching a filter, **When** they run a filtered list command, **Then** they see a clear message indicating no results were found rather than an empty table.

---

### User Story 3 - Analyze Performance Trends (Priority: P3)

A user wants insights that go beyond what Strava shows. They want to see trends over time: weekly/monthly mileage progression, pace improvements, heart rate drift analysis, power curve comparisons, and training load patterns. The CLI computes derived metrics from raw activity data and presents them as tables or terminal-rendered charts.

**Why this priority**: This is the key differentiator — extracting more value from Strava data than Strava itself surfaces. It depends on the activity data retrieval from P2.

**Independent Test**: Can be tested by running analysis commands against synced activity data and verifying that output includes computed metrics (e.g., weekly totals, pace trend direction, zone distribution percentages) that are mathematically correct given the underlying data.

**Acceptance Scenarios**:

1. **Given** an authenticated user with activity history, **When** they run `openactivity strava analyze summary --period weekly`, **Then** they see a weekly breakdown of total distance, duration, elevation, and activity count.
2. **Given** a user with running activities, **When** they run `openactivity strava analyze pace --last 90d`, **Then** they see their average pace trend over the last 90 days with indication of improvement or regression.
3. **Given** a user with heart rate data, **When** they run `openactivity strava analyze zones --type run`, **Then** they see a breakdown of time spent in each heart rate zone across all running activities, with percentage distribution.
4. **Given** a user with cycling power data, **When** they run `openactivity strava analyze power-curve`, **Then** they see their best average power for key durations (5s, 1min, 5min, 20min, 60min).
5. **Given** any analysis command, **When** the user appends `--json`, **Then** the computed data is returned as structured JSON for agent or pipeline consumption.

---

### User Story 4 - Export Activity Data (Priority: P4)

A user wants to export their activity data in various formats for use in other tools, spreadsheets, or for backup. They can export individual activities as GPX or CSV, export bulk data as CSV/JSON, and generate visual charts (PNG/SVG) of performance metrics.

**Why this priority**: Export enables interoperability with other fitness platforms and analysis tools. It extends the value of openactivity beyond the terminal.

**Independent Test**: Can be tested by exporting a known activity and verifying the output file is valid in the target format (e.g., GPX validates against schema, CSV opens in a spreadsheet, chart image renders correctly).

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they run `openactivity strava activity <ID> --export gpx`, **Then** a valid GPX file is written containing the activity's GPS track and sensor data.
2. **Given** an authenticated user, **When** they run `openactivity strava activities export --format csv --after 2025-01-01`, **Then** a CSV file is generated with one row per activity and columns for all key fields.
3. **Given** an authenticated user, **When** they run `openactivity strava analyze summary --period monthly --chart bar --output summary.png`, **Then** a bar chart image is generated showing monthly training volume.
4. **Given** an authenticated user, **When** they run an export command and the output file already exists, **Then** they are warned and must confirm overwrite or use `--force`.

---

### User Story 5 - View Segment Performance (Priority: P5)

A user wants to explore their segment efforts — seeing their best times, comparing against their history, and viewing leaderboard positions. Segments are a core Strava feature and exposing this data in a queryable CLI format allows deeper analysis than Strava's web UI.

**Why this priority**: Segments are valuable but less critical than core activity data and analysis. This adds depth for competitive and data-focused users.

**Independent Test**: Can be tested by listing starred segments, viewing efforts on a specific segment, and verifying times and rankings match expected data.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they run `openactivity strava segments list`, **Then** they see their starred segments with name, distance, average grade, and their PR time.
2. **Given** an authenticated user, **When** they run `openactivity strava segment <ID> efforts`, **Then** they see all their attempts on that segment with date, time, and ranking.
3. **Given** an authenticated user, **When** they run `openactivity strava segment <ID> leaderboard`, **Then** they see the segment leaderboard with optional filters (e.g., `--gender`, `--age-group`, `--friends`).

---

### Edge Cases

- What happens when the user's Strava API rate limit is exceeded? The CLI MUST display a clear message indicating the limit, when it resets, and queue or pause remaining requests.
- What happens when an activity has no GPS data (e.g., treadmill run)? Commands that require GPS (export GPX, map display) MUST gracefully inform the user that GPS data is unavailable rather than failing silently.
- What happens when a user has thousands of activities and requests a full list? The CLI MUST paginate results and support `--limit` and `--offset` flags to control output size.
- What happens when the Strava API is unreachable? The CLI MUST display a clear network error with retry guidance rather than a raw stack trace.
- What happens when an activity lacks heart rate or power data? Analysis commands MUST skip unavailable metrics and inform the user which data streams were missing.
- What happens when the user's access token is revoked externally (e.g., via Strava settings)? The CLI MUST detect the invalid token and prompt re-authentication with a clear message.
- What happens when a free-tier Strava user runs a command that depends on premium data (e.g., detailed zone analysis)? The CLI MUST show all available data and note which missing fields require a Strava subscription, rather than blocking the command.

## Clarifications

### Session 2026-03-13

- Q: Should the CLI query Strava live or sync to local storage? → A: Local sync — `openactivity strava sync` fetches data to a local store; list and analyze commands query locally. Live API calls only during explicit sync.
- Q: Should the CLI ship with a bundled OAuth app or require users to register their own? → A: Users MUST register their own Strava API application and provide their own client ID and client secret. This is standard practice for CLI tools interacting with third-party APIs.
- Q: What unit system should the CLI use for distance, pace, and elevation? → A: Configurable — default to metric (km, m, min/km), with `--units imperial` flag override and a persistent config setting.
- Q: How should the CLI handle Strava free vs premium tier data differences? → A: Graceful degradation — show all available data, and when premium-only fields are absent, inform the user which features require a Strava subscription. Never block a command entirely.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI MUST require users to provide their own Strava API client ID and client secret (from their registered Strava API application). The CLI MUST provide `openactivity strava auth` to configure these credentials, initiate OAuth authorization, store all credentials securely, and handle token refresh automatically.
- **FR-002**: The CLI MUST provide `openactivity strava sync` to fetch activities and related data from the Strava API into local storage. Sync MUST be incremental (only fetch new or updated data since last sync).
- **FR-003**: The CLI MUST provide `openactivity strava activities list` to display activities from local storage in a human-readable table with columns for name, date, type, distance, duration, and elevation gain.
- **FR-004**: The CLI MUST support filtering activities by type (`--type`), date range (`--after`, `--before`), and result limiting (`--limit`, `--offset`). All filtering operates on local data.
- **FR-005**: The CLI MUST provide `openactivity strava activity <ID>` to show detailed activity information including splits, laps, zone distributions, and gear from local storage.
- **FR-006**: Every command that produces data output MUST support `--json` to emit structured JSON to stdout.
- **FR-007**: The CLI MUST provide `openactivity strava analyze` subcommands for computing derived metrics from local data: training volume summaries, pace trends, heart rate zone distributions, and power curves.
- **FR-008**: The CLI MUST provide export capabilities for individual activities (GPX, CSV) and bulk activity lists (CSV, JSON).
- **FR-009**: The CLI MUST provide chart generation for analysis results, outputting PNG or SVG files via `--chart` and `--output` flags.
- **FR-010**: The CLI MUST provide `openactivity strava segments` subcommands for listing starred segments, viewing efforts, and querying leaderboards.
- **FR-011**: All errors MUST be written to stderr with actionable messages. Data output MUST go to stdout.
- **FR-012**: The CLI MUST handle Strava API rate limits during sync by informing the user of the limit status, when it resets, and automatically pausing/resuming sync.
- **FR-013**: The CLI MUST provide `--help` on every command and subcommand with usage examples.
- **FR-014**: The CLI MUST display progress indicators for sync and other network operations that may take longer than 2 seconds.
- **FR-015**: The CLI MUST support `openactivity strava athlete` to display the authenticated user's profile and cumulative stats (year-to-date and all-time totals).
- **FR-016**: The CLI MUST default to metric units (km, m, min/km) and support `--units imperial` on any command that displays distance, pace, elevation, or speed. A persistent config setting MUST allow users to set their preferred unit system globally.

### Key Entities

- **Activity**: A single workout/exercise recorded on Strava. Key attributes: name, type (run, ride, swim, etc.), date, distance, duration, elevation gain, average pace/speed, heart rate data, power data, gear, splits, laps.
- **Athlete**: The authenticated Strava user. Key attributes: name, profile, cumulative stats (total distance, total activities, total elevation), configured heart rate and power zones.
- **Segment**: A defined section of road or trail with a leaderboard. Key attributes: name, distance, average grade, elevation gain, athlete's PR, effort history.
- **Segment Effort**: A single attempt at a segment within an activity. Key attributes: date, elapsed time, moving time, ranking, activity reference.
- **Zone Distribution**: Time spent in each training zone (heart rate or power) for an activity or across activities. Key attributes: zone boundaries, time in zone, percentage of total.
- **Analysis Result**: A computed metric derived from one or more activities. Key attributes: metric name, time period, values, trend direction, comparison baseline.
- **Local Store**: Persistent local storage of synced Strava data. Holds all activity, segment, and athlete data fetched during sync. Tracks last sync timestamp for incremental updates.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can authenticate with Strava and run their first data command within 3 minutes of installation.
- **SC-002**: Listing 50 activities completes and displays results in under 5 seconds on a standard internet connection.
- **SC-003**: All commands produce correct, parseable JSON when `--json` is used, verified by piping output to a JSON validator with zero errors.
- **SC-004**: Analysis commands (summary, pace, zones, power curve) return computed results within 10 seconds for users with up to 1,000 activities.
- **SC-005**: Exported GPX files are valid against the GPX 1.1 schema and open correctly in at least 2 common fitness platforms.
- **SC-006**: Every command and subcommand has `--help` text that includes at least one usage example.
- **SC-007**: Users report that openactivity surfaces at least 3 types of insights not readily visible in Strava's web interface (e.g., cross-activity zone distribution, long-term pace trends, power curve comparisons).
- **SC-008**: An AI agent can discover available commands, authenticate, retrieve activity data, and export results using only `--help` and `--json` output without human guidance.
