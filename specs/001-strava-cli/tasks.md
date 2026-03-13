# Tasks: OpenActivity Strava CLI

**Input**: Design documents from `/specs/001-strava-cli/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/cli-commands.md

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Source**: `src/openactivity/`
- **Tests**: `tests/`
- **Config**: `pyproject.toml`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create pyproject.toml with project metadata, dependencies (typer, rich, sqlalchemy, stravalib, keyring, matplotlib, gpxpy, httpx, tomli-w), console_scripts entry point `openactivity = "openactivity.main:app"`, and dev dependencies (pytest, pytest-cov, ruff, vcrpy)
- [x] T002 Create project directory structure per plan.md: src/openactivity/ with subdirectories cli/, cli/strava/, providers/, providers/strava/, db/, analysis/, export/, config/, auth/, output/ — each with __init__.py
- [x] T003 [P] Configure ruff in pyproject.toml for linting and formatting (line-length, target Python 3.12, select rules)
- [x] T004 [P] Create Makefile with targets: install, dev, test, lint, format, clean

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create root Typer app with global callback for --json and --units flags in src/openactivity/cli/root.py
- [x] T006 Create `openactivity strava` command group as a Typer sub-app in src/openactivity/cli/strava/app.py
- [x] T007 Create main.py entry point that wires root app with strava sub-app in src/openactivity/main.py
- [x] T008 [P] Implement TOML config management (read/write ~/.config/openactivity/config.toml, unit preference, sync settings) in src/openactivity/config/config.py
- [x] T009 [P] Define shared provider Protocol (auth, sync, list_activities methods) in src/openactivity/providers/interface.py
- [x] T010 Define all SQLAlchemy model classes (Athlete, AthleteStats, Activity, Lap, ActivityZone, AthleteZone, ActivityStream, Gear, Segment, SegmentEffort, SyncState) per data-model.md in src/openactivity/db/models.py
- [x] T011 Implement database initialization (SQLite engine, WAL mode, create_all tables, index creation) in src/openactivity/db/database.py
- [x] T012 Implement common query helpers (get_activities with filters, get_activity_by_id, get_athlete, etc.) in src/openactivity/db/queries.py
- [x] T013 [P] Implement Rich table output formatter with configurable columns in src/openactivity/output/table.py
- [x] T014 [P] Implement JSON output helper (serialize to stdout) in src/openactivity/output/json.py
- [x] T015 [P] Implement unit conversion functions (metric/imperial for distance, pace, speed, elevation) in src/openactivity/output/units.py
- [x] T016 [P] Implement structured error output (stderr via Rich, actionable messages, JSON error format) in src/openactivity/output/errors.py

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Authenticate with Strava (Priority: P1) 🎯 MVP

**Goal**: Users can connect their Strava account via OAuth, with credentials stored securely in OS keychain and tokens refreshing automatically.

**Independent Test**: Run `openactivity strava auth`, complete OAuth flow, verify credentials stored. Run any subsequent command to confirm no re-auth prompt.

### Implementation for User Story 1

- [ ] T017 [US1] Implement OS keychain credential storage (store/retrieve/delete client ID, client secret, access token, refresh token, expiry) using keyring library in src/openactivity/auth/keyring.py
- [ ] T018 [US1] Implement Strava OAuth2 flow (authorization URL, localhost callback server, token exchange, token refresh) wrapping stravalib's auth support in src/openactivity/providers/strava/oauth.py
- [ ] T019 [US1] Implement Strava API client wrapper around stravalib with automatic token refresh and rate limit header parsing in src/openactivity/providers/strava/client.py
- [ ] T020 [US1] Implement `openactivity strava auth` command (prompt for client ID/secret on first run, initiate OAuth, store tokens, display confirmation) in src/openactivity/cli/strava/auth.py
- [ ] T021 [US1] Implement `openactivity strava auth revoke` subcommand (delete all stored credentials, display confirmation) in src/openactivity/cli/strava/auth.py
- [ ] T022 [US1] Add --help text with usage examples to auth and auth revoke commands in src/openactivity/cli/strava/auth.py

**Checkpoint**: User Story 1 complete — users can authenticate with Strava and credentials persist

---

## Phase 4: User Story 2 — Browse and Search Activities (Priority: P2)

**Goal**: Users can sync Strava data to local storage, list/filter activities, and view detailed activity information — all from local data after initial sync.

**Independent Test**: Run `openactivity strava sync`, then `openactivity strava activities list` to see activities. Filter with `--type run`. View detail with `openactivity strava activity <ID>`. Verify `--json` output is valid JSON.

### Implementation for User Story 2

- [ ] T023 [US2] Implement stravalib model → SQLAlchemy model transformation functions (activity, laps, zones, streams, athlete, gear) in src/openactivity/providers/strava/transform.py
- [ ] T024 [US2] Implement sync logic with incremental fetch, pagination, rate limit handling (auto-pause/resume), Rich progress display, and SyncState tracking in src/openactivity/providers/strava/sync.py
- [ ] T025 [US2] Implement `openactivity strava sync` command (--full, --detail flags, progress bar, summary output) in src/openactivity/cli/strava/sync.py
- [ ] T026 [US2] Implement `openactivity strava activities list` command with filters (--type, --after, --before, --search, --limit, --offset, --sort) querying local DB in src/openactivity/cli/strava/activities.py
- [ ] T027 [US2] Implement `openactivity strava activity <ID>` command showing detailed view (summary, splits/laps, zone distributions, gear) from local DB in src/openactivity/cli/strava/activities.py
- [ ] T028 [US2] Implement `openactivity strava athlete` command showing profile and cumulative stats (YTD + all-time) from local DB in src/openactivity/cli/strava/athlete.py
- [ ] T029 [US2] Add --help text with usage examples to sync, activities list, activity, and athlete commands in src/openactivity/cli/strava/sync.py, activities.py, athlete.py
- [ ] T030 [US2] Handle edge cases: no activities matching filter (clear message), missing HR/power data (graceful degradation), premium data absence (inform user) in src/openactivity/cli/strava/activities.py

**Checkpoint**: User Stories 1 AND 2 work independently — users can auth, sync, list, filter, and inspect activities

---

## Phase 5: User Story 3 — Analyze Performance Trends (Priority: P3)

**Goal**: Users can run analysis commands that compute derived metrics (training volume, pace trends, zone distributions, power curves) from local data and display as tables.

**Independent Test**: Run `openactivity strava analyze summary --period weekly` and verify weekly totals. Run `openactivity strava analyze zones --type run` and verify zone percentages sum to 100%. Verify `--json` output.

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement training volume aggregation (daily/weekly/monthly totals for distance, duration, elevation, count) in src/openactivity/analysis/summary.py
- [ ] T032 [P] [US3] Implement pace trend computation (average pace per activity over time window, trend direction) in src/openactivity/analysis/pace.py
- [ ] T033 [P] [US3] Implement zone distribution aggregation (aggregate HR/power zone time across activities, compute percentages) in src/openactivity/analysis/zones.py
- [ ] T034 [P] [US3] Implement power curve computation (best average power for 5s, 1min, 5min, 20min, 60min from stream data) in src/openactivity/analysis/power.py
- [ ] T035 [US3] Implement `openactivity strava analyze summary` command (--period, --last, --type flags, table output) in src/openactivity/cli/strava/analyze.py
- [ ] T036 [US3] Implement `openactivity strava analyze pace` command (--last, --type flags, trend display) in src/openactivity/cli/strava/analyze.py
- [ ] T037 [US3] Implement `openactivity strava analyze zones` command (--zone-type, --type, --last flags, distribution table) in src/openactivity/cli/strava/analyze.py
- [ ] T038 [US3] Implement `openactivity strava analyze power-curve` command (--last flag, power table) in src/openactivity/cli/strava/analyze.py
- [ ] T039 [US3] Add --help text with usage examples to all analyze subcommands in src/openactivity/cli/strava/analyze.py
- [ ] T040 [US3] Handle edge cases: no data in time window (clear message), missing streams for power curve (inform user), activities without HR data skipped with notice in src/openactivity/cli/strava/analyze.py

**Checkpoint**: User Stories 1-3 work — users can auth, sync, browse, and analyze their data

---

## Phase 6: User Story 4 — Export Activity Data (Priority: P4)

**Goal**: Users can export individual activities as GPX/CSV, bulk export activity lists, and generate chart images (PNG/SVG) from analysis results.

**Independent Test**: Run `openactivity strava activity <ID> --export gpx --output test.gpx` and validate GPX file. Run `openactivity strava analyze summary --chart bar --output chart.png` and verify image renders.

### Implementation for User Story 4

- [ ] T041 [P] [US4] Implement GPX file generation from activity stream data (latlng, altitude, heartrate, time) using gpxpy in src/openactivity/export/gpx.py
- [ ] T042 [P] [US4] Implement CSV export for single activity and bulk activity lists in src/openactivity/export/csv.py
- [ ] T043 [P] [US4] Implement chart generation (bar, line, scatter, pie charts as PNG/SVG) using matplotlib in src/openactivity/export/chart.py
- [ ] T044 [US4] Add --export and --output flags to `openactivity strava activity <ID>` command for GPX/CSV export in src/openactivity/cli/strava/activities.py
- [ ] T045 [US4] Implement `openactivity strava activities export` command (--format, --output, --after, --before, --type, --force flags) in src/openactivity/cli/strava/export.py
- [ ] T046 [US4] Add --chart and --output flags to all analyze subcommands (summary, pace, zones, power-curve) in src/openactivity/cli/strava/analyze.py
- [ ] T047 [US4] Implement file overwrite protection (warn if file exists, require --force or confirmation) in src/openactivity/export/file_utils.py (new file)
- [ ] T048 [US4] Handle edge cases: activity without GPS data for GPX export (clear error), no activities matching export filters (clear message) in src/openactivity/cli/strava/export.py
- [ ] T049 [US4] Add --help text with usage examples to export commands in src/openactivity/cli/strava/export.py

**Checkpoint**: User Stories 1-4 work — full data pipeline from auth → sync → browse → analyze → export

---

## Phase 7: User Story 5 — View Segment Performance (Priority: P5)

**Goal**: Users can view starred segments, their effort history on segments, and segment leaderboards.

**Independent Test**: Run `openactivity strava segments list` and verify starred segments displayed. Run `openactivity strava segment <ID> efforts` and verify effort history.

### Implementation for User Story 5

- [ ] T050 [US5] Implement `openactivity strava segments list` command (--type, --limit flags, table output from local DB) in src/openactivity/cli/strava/segments.py
- [ ] T051 [US5] Implement `openactivity strava segment <ID> efforts` command (--limit flag, effort history table) in src/openactivity/cli/strava/segments.py
- [ ] T052 [US5] Implement `openactivity strava segment <ID> leaderboard` command (--gender, --age-group, --friends, --limit flags) in src/openactivity/cli/strava/segments.py
- [ ] T053 [US5] Add segment and segment effort sync to the sync command (fetch starred segments, efforts) in src/openactivity/providers/strava/sync.py
- [ ] T054 [US5] Add --help text with usage examples to all segment subcommands in src/openactivity/cli/strava/segments.py

**Checkpoint**: All user stories complete and independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T055 [P] Add shell completion generation (bash, zsh, fish) via Typer's built-in completion support in src/openactivity/main.py
- [ ] T056 [P] Add version command (`openactivity --version`) using Typer version callback in src/openactivity/cli/root.py
- [ ] T057 Review and ensure all commands write errors to stderr and data to stdout consistently
- [ ] T058 Review and ensure all commands support --json with valid, parseable JSON output
- [ ] T059 Review and ensure all commands have --help text with at least one usage example
- [ ] T060 [P] Add README.md with installation instructions, quickstart guide, and command reference
- [ ] T061 Run quickstart.md validation — walk through every command in quickstart.md and verify expected behavior

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — no dependencies on other stories
- **User Story 2 (Phase 4)**: Depends on Foundational + US1 (needs auth to sync)
- **User Story 3 (Phase 5)**: Depends on US2 (needs synced local data to analyze)
- **User Story 4 (Phase 6)**: Depends on US2 (needs local data to export) and US3 (needs analysis for charts)
- **User Story 5 (Phase 7)**: Depends on US2 (needs sync infrastructure)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (Auth)**: Independent — gateway for all other stories
- **US2 (Browse/Sync)**: Requires US1 (auth) — gateway for data-dependent stories
- **US3 (Analyze)**: Requires US2 (synced data) — independent of US4, US5
- **US4 (Export)**: Requires US2 (data) + US3 (analysis for chart export)
- **US5 (Segments)**: Requires US2 (sync infrastructure) — independent of US3, US4

### Within Each User Story

- Transform/models before services
- Services before CLI commands
- Core implementation before edge case handling
- Edge cases before help text polish
- Story complete before moving to next priority

### Parallel Opportunities

- Phase 1: T003, T004 can run in parallel
- Phase 2: T008, T009 in parallel; T013, T014, T015, T016 in parallel
- Phase 5: T031, T032, T033, T034 (all analysis engines) can run in parallel
- Phase 6: T041, T042, T043 (all export implementations) can run in parallel

---

## Parallel Example: User Story 3

```bash
# All analysis engines can be built in parallel (different files, no deps):
Task: "Implement training volume aggregation in src/openactivity/analysis/summary.py"
Task: "Implement pace trend computation in src/openactivity/analysis/pace.py"
Task: "Implement zone distribution aggregation in src/openactivity/analysis/zones.py"
Task: "Implement power curve computation in src/openactivity/analysis/power.py"

# Then wire CLI commands sequentially (same file):
Task: "Implement analyze summary command in src/openactivity/cli/strava/analyze.py"
Task: "Implement analyze pace command in src/openactivity/cli/strava/analyze.py"
Task: "Implement analyze zones command in src/openactivity/cli/strava/analyze.py"
Task: "Implement analyze power-curve command in src/openactivity/cli/strava/analyze.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Auth)
4. Complete Phase 4: User Story 2 (Sync + Browse)
5. **STOP and VALIDATE**: Auth → Sync → List → Detail flow works end-to-end
6. This is a usable CLI that can auth, sync, and display Strava data

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 (Auth) → Users can connect Strava
3. US2 (Sync + Browse) → Users can view their data (MVP!)
4. US3 (Analyze) → Users get insights beyond Strava
5. US4 (Export) → Users can export data and charts
6. US5 (Segments) → Users get segment analysis
7. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All distances/times stored in metric internally; conversion at display time only
- No network calls outside of `sync` and `auth` commands
- stravalib handles most Strava API complexity (pagination, model deserialization)
