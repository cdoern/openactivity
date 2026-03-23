# Feature Specification: Garmin FIT File Import

**Feature Branch**: `010-garmin-provider`
**Created**: 2026-03-23
**Updated**: 2026-03-23
**Status**: Draft
**Input**: User description: "Add Garmin Connect as a second data provider, following the existing provider interface pattern."

## Context & Approach

**Original Plan**: Use Garmin's unofficial API (`garminconnect` library) for automated sync.

**Reality**: Garmin actively blocks automated API access through rate limiting and bot detection. Even with valid credentials, API requests are unreliable and frequently result in 24-48 hour bans.

**Solution**: Use FIT file parsing instead of API access:
- FIT files are Garmin's native activity format
- 100% reliable (no API calls)
- Contains all activity data (GPS, HR, power, cadence, etc.)
- Available from multiple sources (device, Garmin Connect folder, bulk export)

**Trade-off**: Advanced health metrics (HRV, Body Battery, detailed sleep) are NOT in FIT files. Users can import these separately from Garmin's bulk export CSVs.

---

## User Scenarios & Testing

### User Story 1 - Import from Connected Device (Priority: P1) 🎯 MVP

As a user with a Garmin device, I want to import activities directly from my watch when it's connected via USB so I can analyze my workouts locally without any API hassles.

**Why this priority**: Most straightforward and reliable method. Works immediately with no setup beyond connecting device.

**Independent Test**: User connects Garmin device via USB and runs `openactivity garmin import --from-device`. Activities from the device appear in the local database. Running `openactivity activities list` shows them.

**Acceptance Scenarios**:

1. **Given** a Garmin device is connected via USB, **When** the user runs `openactivity garmin import --from-device`, **Then** all FIT files from the device are parsed and imported as activities
2. **Given** some activities were previously imported, **When** the user imports again from device, **Then** only new activities are imported (duplicates are skipped)
3. **Given** no device is connected, **When** the user runs import from device, **Then** they see a helpful error with troubleshooting steps
4. **Given** import completes, **When** the command finishes, **Then** the user sees a summary of files processed, activities imported, and any errors

---

### User Story 2 - Import from Garmin Connect Folder (Priority: P1)

As a user who syncs via Garmin Express, I want to import activities from the local Garmin Connect folder so I can get my data without connecting my device every time.

**Why this priority**: Convenient for users who already use Garmin Express for cloud sync. Files appear automatically after sync.

**Independent Test**: User syncs device with Garmin Express, then runs `openactivity garmin import --from-connect`. Activities appear in local database.

**Acceptance Scenarios**:

1. **Given** Garmin Express is installed and has synced data, **When** the user runs `openactivity garmin import --from-connect`, **Then** FIT files from the Garmin Connect folder are imported
2. **Given** the Garmin Connect folder doesn't exist, **When** the user attempts to import, **Then** they see a helpful error explaining how to set up Garmin Express
3. **Given** new activities are synced via Garmin Express, **When** the user re-runs import from Connect folder, **Then** only new activities are imported

---

### User Story 3 - Import from Bulk Export ZIP (Priority: P1)

As a user, I want to import my complete Garmin history from a bulk export ZIP file so I can migrate all my historical data at once.

**Why this priority**: Essential for initial setup and historical data migration. Garmin's official export is the most reliable way to get all data.

**Independent Test**: User downloads bulk export from Garmin (Settings → Data Management → Export Your Data), then runs `openactivity garmin import --from-zip ~/Downloads/export.zip`. All activities are imported.

**Acceptance Scenarios**:

1. **Given** a Garmin bulk export ZIP file, **When** the user runs `openactivity garmin import --from-zip PATH`, **Then** all FIT files in the ZIP are extracted and imported
2. **Given** the ZIP contains thousands of activities, **When** import runs, **Then** progress is shown and the process completes successfully
3. **Given** an invalid or corrupted ZIP, **When** import is attempted, **Then** a clear error message is shown

---

### User Story 4 - Import from Custom Directory (Priority: P2)

As a user with FIT files in a custom location, I want to import from any directory so I have flexibility in how I organize my data.

**Why this priority**: Useful but not critical - most users will use device/Connect/ZIP options.

**Independent Test**: User places FIT files in a custom folder and runs `openactivity garmin import --from-directory ~/my-activities/`. Activities are imported.

**Acceptance Scenarios**:

1. **Given** FIT files in a custom directory, **When** the user runs `openactivity garmin import --from-directory PATH`, **Then** all FIT files (recursive search) are imported
2. **Given** a directory with mixed file types, **When** import runs, **Then** only .fit/.FIT files are processed, others are ignored

---

### User Story 5 - Unified Activity Commands (Priority: P2)

As a user with both Strava and Garmin data, I want to use `openactivity activity <ID>` and `openactivity activities list` to see all my activities regardless of provider.

**Why this priority**: Improves UX but requires data from both providers first.

**Independent Test**: User runs `openactivity activities list` and sees activities from both providers with badges. Running `openactivity activity <ID>` works with any ID.

**Acceptance Scenarios**:

1. **Given** activities from both Strava and Garmin, **When** the user runs `openactivity activities list`, **Then** they see a merged view with provider badges
2. **Given** an activity ID, **When** the user runs `openactivity activity <ID>`, **Then** the system auto-detects the provider and shows details
3. **Given** the user wants to filter, **When** they use `--provider garmin`, **Then** only Garmin activities are shown

---

### Edge Cases

- What happens when a FIT file is corrupted or unparseable?
- How does the system handle FIT files that aren't activities (monitoring files, settings files)?
- What if the same activity is imported twice from different sources (device and ZIP)?
- How are provider_ids assigned to ensure uniqueness?
- What happens when no FIT files are found in the specified location?

---

## Functional Requirements *(mandatory)*

### Import Sources

**FR-001**: System shall support importing FIT files from a connected Garmin device (USB)
**FR-002**: System shall support importing FIT files from Garmin Connect local folder (created by Garmin Express)
**FR-003**: System shall support importing FIT files from Garmin bulk export ZIP files
**FR-004**: System shall support importing FIT files from any custom directory (recursive search)
**FR-005**: System shall detect and skip already-imported activities (based on provider_id)

### FIT File Parsing

**FR-006**: System shall parse FIT files using the `fitparse` library (battle-tested, widely used)
**FR-007**: System shall extract activity metadata: name, type, start time, distance, duration, elevation
**FR-008**: System shall extract activity metrics: heart rate, power, cadence, speed (when available)
**FR-009**: System shall handle missing or optional fields gracefully (e.g., power data not on all devices)
**FR-010**: System shall skip non-activity FIT files (monitoring, settings) without errors

### Data Storage

**FR-011**: Imported activities shall be stored with provider='garmin' in the activities table
**FR-012**: Activities shall have unique provider_ids generated from file metadata (timestamp-based)
**FR-013**: System shall normalize Garmin sport types to standard types (Run, Ride, Swim, etc.)
**FR-014**: System shall preserve Garmin-specific sport type in sport_type field

### User Experience

**FR-015**: Import command shall show progress (files processed, activities imported, skipped, errors)
**FR-016**: Import command shall provide helpful error messages with troubleshooting steps
**FR-017**: Import command shall complete in reasonable time (thousands of activities < 5 minutes)
**FR-018**: System shall provide clear documentation on how to get FIT files from each source

### Multi-Provider Support

**FR-019**: Unified `activities list` command shall show Garmin and Strava activities together
**FR-020**: Unified `activity <ID>` command shall work with activity IDs from any provider
**FR-021**: Activities list shall display provider badges ([Garmin], [Strava], [Garmin+Strava] for linked)
**FR-022**: System shall support filtering by provider using --provider flag

---

## Success Criteria *(mandatory)*

**Objective**: Enable users to reliably import and analyze Garmin activity data without API dependency.

**Measurable Outcomes**:

1. **Import Reliability**: 100% success rate for valid FIT files (no API failures/rate limits)
2. **Import Speed**: Process 1000 FIT files in under 2 minutes
3. **Data Completeness**: All standard activity fields populated (distance, time, HR, etc.) from FIT data
4. **User Experience**: Users can complete initial import (bulk export ZIP) in under 5 commands
5. **Zero API Dependency**: No network requests required for activity import

**Qualitative Outcomes**:

- Users are not blocked by Garmin's rate limiting
- Import process is self-service (no authentication required)
- Clear path from "I have a Garmin" to "I have all my data"
- Works offline (no internet required after downloading export)

---

## Limitations & Out of Scope

**Health Data NOT in FIT Files** (deferred to future work):
- Heart Rate Variability (HRV)
- Body Battery scores
- Detailed sleep phase analysis
- Stress scores
- Advanced physiological metrics

**Rationale**: These metrics are proprietary Garmin calculations stored only in their cloud database, not in device FIT files. Future enhancement could parse CSV files from Garmin's bulk export to import this data separately.

**No Automated Sync**: Unlike Strava (which has OAuth API), there is no automated background sync for Garmin. Users must manually import FIT files periodically.

**Rationale**: Garmin's API is unreliable and results in user bans. Manual FIT import is the only sustainable approach.

---

## Assumptions *(if applicable)*

1. **FIT File Availability**: Users can obtain FIT files via USB device connection, Garmin Express, or bulk export
2. **Library Reliability**: `fitparse` library correctly parses Garmin FIT files (well-established, used in production by many projects)
3. **File Format Stability**: Garmin's FIT file format remains stable (it's a published standard: FIT SDK)
4. **User Technical Ability**: Users can connect USB devices, download ZIP files, and specify file paths
5. **Single Athlete**: Initial implementation assumes one athlete per database (multi-athlete support is future work)

---

## Dependencies & Constraints

**Technical Dependencies**:
- `fitparse>=1.2.0` - FIT file parsing library
- Python 3.12+ - Current project requirement
- SQLAlchemy models already support multi-provider (added in earlier work)

**Constraints**:
- No network access required (offline-first approach)
- Must work cross-platform (Linux, macOS, Windows device mount points differ)
- FIT files only contain activity data, not advanced health metrics
- Cannot automate discovery of new activities (user must initiate import)

**Related Features**:
- Depends on database schema changes (Activity.provider, Activity.provider_id fields)
- Works alongside Strava provider (shared unified commands)
- Future: CSV import for health data from Garmin bulk export

---

## Non-Functional Requirements

**Performance**:
- Import 1000 FIT files in < 2 minutes (average hardware)
- Memory usage < 500MB for large imports (streaming file processing)
- Incremental import completes in < 5 seconds (checking for duplicates)

**Reliability**:
- 100% success rate for valid FIT files
- Graceful handling of corrupted files (skip with error message)
- No data loss during import errors (transaction rollback)

**Usability**:
- Clear help text for each import option
- Automatic device detection (no manual path entry when possible)
- Progress feedback for long operations (thousands of files)

**Maintainability**:
- Use established library (`fitparse`) rather than custom parser
- Minimal code surface area (< 500 lines for all import logic)
- Clear separation: parsing (fit_parser.py) vs importing (importer.py) vs CLI (import_cmd.py)
