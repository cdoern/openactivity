# Tasks: Personal Records Database

**Input**: Design documents from `/specs/004-personal-records/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-commands.md

**Tests**: Unit tests included as requested (test_records.py specified in plan.md).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database models and constants shared by all user stories

- [x] T001 Add PersonalRecord and CustomDistance models to src/openactivity/db/models.py
- [x] T002 Add pr_scanned boolean column to Activity model in src/openactivity/db/models.py
- [x] T003 Add record query helpers (get_personal_records, get_records_by_distance, get_custom_distances) to src/openactivity/db/queries.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core scanning algorithm and record management logic that ALL user stories depend on

**⚠️ CRITICAL**: No user story CLI work can begin until this phase is complete

- [x] T004 Create src/openactivity/analysis/records.py with standard distance/power constants (RUNNING_DISTANCES, CYCLING_POWER_DURATIONS)
- [x] T005 Implement sliding window distance PR detection function `find_best_effort_for_distance(distance_stream, time_stream, target_meters)` in src/openactivity/analysis/records.py
- [x] T006 Implement best power detection function `find_best_power_for_duration(watts_stream, target_seconds)` in src/openactivity/analysis/records.py
- [x] T007 Implement `scan_activity_for_records(session, activity, distances)` orchestrator that runs sliding window for all distances/durations and persists PersonalRecord entries in src/openactivity/analysis/records.py
- [x] T008 Implement `scan_all_activities(session, full=False)` that queries unscanned activities, calls scan_activity_for_records for each, and marks pr_scanned=True in src/openactivity/analysis/records.py

**Checkpoint**: Core scanning engine ready — CLI commands can now be built on top

---

## Phase 3: User Story 1 — Scan Activities and View Current PRs (Priority: P1) 🎯 MVP

**Goal**: User can scan their synced activities for PRs and view current best efforts in a table

**Independent Test**: Run scan command, then list command — verify correct best efforts appear for each standard distance

### Tests for User Story 1

- [x] T009 [P] [US1] Write unit tests for sliding window algorithm (edge cases: short activity, exact distance match, multiple segments) in tests/unit/test_records.py
- [x] T010 [P] [US1] Write unit tests for record management (new PR insertion, PR update with is_current flag, no-update when slower) in tests/unit/test_records.py

### Implementation for User Story 1

- [x] T011 [US1] Create src/openactivity/cli/strava/records.py with typer app and `scan` command (--full flag, progress bar, summary output, --json support)
- [x] T012 [US1] Implement `list` command in src/openactivity/cli/strava/records.py (--type filter, Rich table output per contracts/cli-commands.md, --json support)
- [x] T013 [US1] Register records command group in src/openactivity/cli/strava/app.py

**Checkpoint**: User Story 1 fully functional — scan and list commands work end-to-end

---

## Phase 4: User Story 2 — View PR Progression History (Priority: P2)

**Goal**: User can see how their PR for a specific distance has improved over time

**Independent Test**: Scan activities with multiple improving efforts at a distance, run history command, verify chronological progression with correct deltas

### Implementation for User Story 2

- [x] T014 [US2] Implement `get_pr_history(session, distance_type)` query helper in src/openactivity/db/queries.py
- [x] T015 [US2] Implement `history` command in src/openactivity/cli/strava/records.py (--distance flag, Rich table with progression/deltas per contracts/cli-commands.md, --json support)

**Checkpoint**: User Stories 1 AND 2 both work independently

---

## Phase 5: User Story 3 — Add Custom Distances (Priority: P3)

**Goal**: User can add/remove custom distances for PR tracking beyond the standard set

**Independent Test**: Add a custom distance, run scan, verify custom distance appears in PR list

### Implementation for User Story 3

- [x] T016 [P] [US3] Implement `add_custom_distance(session, label, meters)` and `remove_custom_distance(session, label)` in src/openactivity/analysis/records.py
- [x] T017 [US3] Implement `add-distance` command in src/openactivity/cli/strava/records.py (positional args: LABEL, METERS; validation against standard distances)
- [x] T018 [US3] Implement `remove-distance` command in src/openactivity/cli/strava/records.py (positional arg: LABEL; prevent removal of standard distances)
- [x] T019 [US3] Update scan logic to merge custom distances with standard distances in src/openactivity/analysis/records.py

**Checkpoint**: All user stories 1-3 independently functional

---

## Phase 6: User Story 4 — JSON Output for Agent Consumption (Priority: P4)

**Goal**: All records commands produce valid structured JSON output when --json flag is used

**Independent Test**: Run any records command with --json and verify valid, parseable JSON

### Implementation for User Story 4

- [x] T020 [US4] Verify and finalize JSON output for scan command (scanned count, new/updated records) in src/openactivity/cli/strava/records.py
- [x] T021 [US4] Verify and finalize JSON output for list command (all PR records with distances, times, paces, dates) in src/openactivity/cli/strava/records.py
- [x] T022 [US4] Verify and finalize JSON output for history command (progression array with deltas) in src/openactivity/cli/strava/records.py

**Checkpoint**: All commands produce correct JSON output

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [x] T023 Run all unit tests and fix any failures in tests/unit/test_records.py
- [x] T024 Run linter (ruff check) and fix any issues across all modified files
- [x] T025 Validate quickstart.md scenarios work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001-T003 are sequential (same files)
- **Foundational (Phase 2)**: Depends on Phase 1 — T004-T008 sequential (same file, building on each other)
- **US1 (Phase 3)**: Depends on Phase 2 — T009/T010 parallel (tests), then T011-T013 sequential
- **US2 (Phase 4)**: Depends on Phase 2 — can run parallel with US1 but logically follows it
- **US3 (Phase 5)**: Depends on Phase 2 — T016 parallel, then T017-T019 sequential
- **US4 (Phase 6)**: Depends on US1/US2/US3 — validates JSON output across all commands
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Core MVP — no dependencies on other stories
- **US2 (P2)**: Requires scan infrastructure from Phase 2, independent of US1 CLI
- **US3 (P3)**: Requires scan infrastructure from Phase 2, independent of US1/US2
- **US4 (P4)**: Validates JSON across US1/US2/US3 commands — should come last

### Parallel Opportunities

- T009 and T010 can run in parallel (different test classes, same file)
- T016 can run in parallel with US1/US2 implementation
- US1, US2, US3 implementation phases are largely independent after Phase 2

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (models + queries)
2. Complete Phase 2: Foundational (scanning algorithm)
3. Complete Phase 3: User Story 1 (scan + list commands)
4. **STOP and VALIDATE**: Test scan + list independently
5. Proceed to remaining stories

### Incremental Delivery

1. Setup + Foundational → Scanning engine ready
2. Add US1 → scan + list commands → MVP!
3. Add US2 → history command
4. Add US3 → custom distances
5. Add US4 → JSON validation
6. Polish → tests pass, lint clean

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Existing `analysis/power.py` has sliding window logic to reference (but don't import directly — extract pattern)
- Stream data is JSON-encoded bytes in LargeBinary column, deserialized with `json.loads()`
- Use `get_global_state()` for --json flag detection
- Use `exit_with_error()` for error messages
- Follow existing CLI patterns from `cli/strava/analyze.py`
