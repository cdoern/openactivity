# Feature Specification: Garmin Connect Provider

**Feature Branch**: `010-garmin-provider`
**Created**: 2026-03-23
**Status**: Draft
**Input**: User description: "Add Garmin Connect as a second data provider, following the existing provider interface pattern. This unlocks HRV, Body Battery, sleep, respiration, and other health metrics that Strava doesn't have."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Authenticate with Garmin Connect (Priority: P1)

As a user with a Garmin Connect account, I want to authenticate the CLI with my Garmin credentials so I can access my Garmin fitness and health data locally.

**Why this priority**: Without authentication, no Garmin data can be synced. This is the foundational requirement for all other Garmin features.

**Independent Test**: User runs `openactivity garmin auth`, provides username and password, and receives confirmation that credentials are stored. Subsequent commands can access Garmin data without re-authentication.

**Acceptance Scenarios**:

1. **Given** the user has a valid Garmin Connect account, **When** they run `openactivity garmin auth` and provide valid credentials, **Then** credentials are securely stored in the system keyring and a success message is displayed
2. **Given** the user provides invalid credentials, **When** they run `openactivity garmin auth`, **Then** an error message is displayed and they can retry
3. **Given** credentials are already stored, **When** the user runs `openactivity garmin auth` again, **Then** they are prompted to confirm overwriting existing credentials
4. **Given** the user wants to check auth status, **When** they run `openactivity garmin auth --status`, **Then** they see whether they are authenticated and when credentials were last verified

---

### User Story 2 - Sync Garmin Activities (Priority: P1)

As a user, I want to sync my Garmin activities to local storage so I can analyze my workouts offline alongside my Strava data.

**Why this priority**: Activity sync is the core value proposition - without it, users cannot access their Garmin workout data. This must work independently before any advanced features.

**Independent Test**: User runs `openactivity garmin sync`, and their recent Garmin activities appear in the local database. Running `openactivity activities list` shows a merged view with both Strava and Garmin activities with provider badges.

**Acceptance Scenarios**:

1. **Given** the user is authenticated with Garmin, **When** they run `openactivity garmin sync` for the first time, **Then** all recent activities from Garmin are downloaded and stored locally
2. **Given** the user has previously synced, **When** they run `openactivity garmin sync` again, **Then** only new or updated activities since last sync are downloaded (incremental sync)
3. **Given** an activity exists in both Strava and Garmin, **When** activities are synced from both providers, **Then** the system detects the duplicate and links them as the same activity
4. **Given** the user runs sync with no auth, **When** they attempt to sync, **Then** they receive an error directing them to run `openactivity garmin auth` first

---

### User Story 3 - Sync Garmin Health Data (Priority: P2)

As a user, I want to sync my daily health metrics (HRV, Body Battery, sleep, stress) from Garmin so I can track my recovery and readiness over time.

**Why this priority**: Health data is unique to Garmin and provides value beyond basic activity tracking, but activities must sync first (P1) for this data to be contextually useful.

**Independent Test**: User runs `openactivity garmin sync` and their daily health summaries are stored locally. User can query `openactivity garmin daily --last 7d` to see recent health metrics.

**Acceptance Scenarios**:

1. **Given** the user is authenticated with Garmin, **When** they run `openactivity garmin sync`, **Then** daily summaries (HRV, Body Battery, stress, resting HR, respiration, SpO2, steps, sleep score) are downloaded and stored
2. **Given** sleep data is available, **When** daily summaries are synced, **Then** sleep sessions with detailed phase breakdowns (deep/light/REM/awake) are stored
3. **Given** the user wants to view recent health data, **When** they run `openactivity garmin daily --last 7d`, **Then** they see a summary of health metrics for the past 7 days

---

### User Story 4 - Unified Activity Commands (Priority: P2)

As a user with both Strava and Garmin accounts, I want to use simple commands like `openactivity activity <ID>` and `openactivity activities list` that work across both providers so I don't need to remember which provider an activity came from.

**Why this priority**: Improves user experience significantly but requires both providers to be functional first. Makes the tool feel cohesive rather than fragmented.

**Independent Test**: User runs `openactivity activities list` and sees activities from all providers in a single view with provider badges. User runs `openactivity activity <ID>` with any activity ID and sees details regardless of provider.

**Acceptance Scenarios**:

1. **Given** the user has synced activities from both Strava and Garmin, **When** they run `openactivity activities list`, **Then** they see a merged chronological list with provider badges indicating source (Strava/Garmin/Both for duplicates)
2. **Given** an activity exists in the database, **When** the user runs `openactivity activity <ID>` with any valid ID (Strava or Garmin), **Then** the system auto-detects the provider and displays activity details
3. **Given** an activity is linked as a duplicate, **When** viewed, **Then** the display shows it came from both providers and which was the primary source
4. **Given** the user filters activities, **When** they use `--provider strava` or `--provider garmin`, **Then** only activities from that provider are shown

---

### User Story 5 - View Athlete Profile from Garmin (Priority: P3)

As a user, I want to view my Garmin athlete profile information so I can verify my account details and settings are correct.

**Why this priority**: Nice to have for verification but not critical for core functionality. Most users care more about activity and health data.

**Independent Test**: User runs `openactivity garmin athlete` and sees their Garmin profile information (name, age, gender, weight, max HR, zones).

**Acceptance Scenarios**:

1. **Given** the user is authenticated, **When** they run `openactivity garmin athlete`, **Then** they see their Garmin Connect profile information including name, age, gender, and fitness settings
2. **Given** the user wants JSON output, **When** they run `openactivity garmin athlete --json`, **Then** they receive profile data in JSON format

---

### Edge Cases

- What happens when Garmin API is down or rate-limited during sync?
- How does the system handle activities that exist in both providers but with slightly different timestamps or durations?
- What if a user changes their Garmin password - how do they update stored credentials?
- How does deduplication work when one provider has more detailed data than the other?
- What happens when health data is missing for certain days?
- How are activities matched for deduplication when types differ slightly between providers (e.g., "Run" vs "Running")?

## Requirements *(mandatory)*

### Functional Requirements

#### Authentication & Credentials
- **FR-001**: System MUST provide a command to authenticate with Garmin Connect using username and password
- **FR-002**: System MUST store Garmin credentials securely in the system keyring
- **FR-003**: System MUST validate credentials on first use and provide clear error messages for authentication failures
- **FR-004**: System MUST allow users to check authentication status without triggering a full sync

#### Activity Syncing
- **FR-005**: System MUST sync activities from Garmin Connect to local storage
- **FR-006**: System MUST support incremental sync, fetching only new or updated activities after the initial sync
- **FR-007**: System MUST store activity provider (Strava/Garmin) and provider-specific ID in the database
- **FR-008**: System MUST detect and link duplicate activities from multiple providers based on start time (within 60 seconds), activity type, and duration (within 5% tolerance)
- **FR-009**: System MUST sync activity details including: distance, duration, type, start time, elevation, heart rate data, pace/speed, calories
- **FR-010**: System MUST handle activity types consistently across providers (map Garmin types to standardized internal types)

#### Health Data Syncing
- **FR-011**: System MUST sync daily health summaries from Garmin including: resting heart rate, HRV, Body Battery, stress score, sleep score, steps, respiration rate, SpO2
- **FR-012**: System MUST sync sleep session details including: start/end times, total duration, deep/light/REM/awake phase durations, sleep score
- **FR-013**: System MUST handle missing health data gracefully (some metrics may not be available for all users or all days)

#### Provider-Agnostic Commands
- **FR-014**: System MUST provide `openactivity activity <ID>` command that works with IDs from any provider
- **FR-015**: System MUST auto-detect which provider an activity belongs to when given an ID
- **FR-016**: System MUST provide `openactivity activities list` command that shows merged view from all providers
- **FR-017**: System MUST display provider badges in activity lists (Strava/Garmin/Both)
- **FR-018**: System MUST allow filtering by provider using `--provider` flag
- **FR-019**: System MUST continue to support existing provider-specific commands (`openactivity strava segments`, etc.)

#### Command Structure
- **FR-020**: System MUST provide new command group `openactivity garmin` with subcommands: auth, sync, athlete, activities, daily
- **FR-021**: System MUST support `openactivity garmin auth` for authentication
- **FR-022**: System MUST support `openactivity garmin sync` for data synchronization
- **FR-023**: System MUST support `openactivity garmin athlete` to view profile
- **FR-024**: System MUST support `openactivity garmin daily` to view health data
- **FR-025**: System MUST support `openactivity garmin activities list` as provider-specific alternative to unified list

#### Data Management
- **FR-026**: System MUST maintain referential integrity between activities and their provider sources
- **FR-027**: System MUST persist sync state to enable incremental updates
- **FR-028**: System MUST handle concurrent syncs gracefully (e.g., if user runs both `strava sync` and `garmin sync` simultaneously)

### Key Entities

- **GarminDailySummary**: Daily health metrics snapshot containing date, resting HR, HRV, Body Battery level, stress score, sleep score, step count, respiration rate, SpO2 percentage. One record per day per user.

- **GarminSleepSession**: Sleep tracking data containing start timestamp, end timestamp, total duration, deep sleep duration, light sleep duration, REM sleep duration, awake duration, sleep quality score. May have multiple sessions per day (e.g., naps).

- **Activity (Enhanced)**: Existing activity entity extended with provider field (enum: strava/garmin) and provider_id field to support multi-provider data. Enables deduplication and source tracking.

- **ActivityDuplication**: Link table connecting duplicate activities from different providers, storing which activity is primary and metadata about the match confidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can authenticate with Garmin Connect in under 1 minute
- **SC-002**: Initial sync of 100 activities completes in under 5 minutes
- **SC-003**: Incremental sync detects and syncs new activities within 30 seconds of command execution
- **SC-004**: Activity deduplication correctly identifies at least 95% of matching activities across providers
- **SC-005**: Users can view merged activity lists from all providers without knowing provider-specific commands
- **SC-006**: Health data (HRV, Body Battery, sleep) syncs successfully for users who have Garmin devices that track these metrics
- **SC-007**: System handles Garmin API rate limits and errors gracefully without data loss
- **SC-008**: All existing Strava-specific commands continue to work unchanged after Garmin provider is added

## Assumptions

- Garmin Connect API access via `garminconnect` Python library provides sufficient endpoints for activity and health data
- Users have valid Garmin Connect accounts with associated devices that track activities and health metrics
- Activity deduplication tolerance (60 seconds time difference, 5% duration difference) is sufficient for most real-world cases
- System keyring is available on user's platform for secure credential storage
- Garmin and Strava use compatible activity type taxonomies that can be normalized
- Users understand that some Garmin devices may not track all health metrics (HRV, Body Battery, etc.)
- Database schema can be modified to add provider fields without breaking existing Strava functionality

## Dependencies

- Requires `garminconnect` Python library for Garmin Connect API access
- Requires system keyring for secure credential storage
- Database migration to add `provider` and `provider_id` fields to Activity model
- Existing Strava sync infrastructure as a reference implementation pattern

## Out of Scope

- Real-time sync or webhooks (both Strava and Garmin use polling-based sync)
- Uploading activities from CLI to Garmin Connect (read-only access)
- Advanced health analytics beyond raw data display (e.g., trend analysis, predictions)
- Two-factor authentication for Garmin (not supported by garminconnect library)
- Garmin Training Plans or Workout creation
- Live tracking or real-time activity updates
- Migration tools for moving data between providers
