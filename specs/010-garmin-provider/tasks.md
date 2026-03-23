# Tasks: Garmin FIT File Import

**Input**: Design documents from `/specs/010-garmin-provider/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup ✅ COMPLETE

**Purpose**: Add dependencies and create directory structure

- [X] T001 Replace garminconnect with fitparse in pyproject.toml dependencies
- [X] T002 Create provider directory structure at src/openactivity/providers/garmin/
- [X] T003 Create CLI directory structure at src/openactivity/cli/garmin/

---

## Phase 2: Foundational (Database Migration) ✅ COMPLETE

**Purpose**: Extend database schema for multi-provider support. MUST complete before ANY user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Add provider and provider_id fields to Activity model in src/openactivity/db/models.py
- [X] T005 Create database migration script in src/openactivity/db/migrations/_001_add_garmin_support.py
- [X] T006 Add migration execution to database initialization in src/openactivity/db/database.py

**Checkpoint**: Database schema ready - all user stories can now proceed in parallel.

---

## Phase 3: Core FIT Parsing (Foundation for All Import Methods) ✅ COMPLETE

**Purpose**: Implement FIT file parsing that all import methods will use.

**⚠️ CRITICAL**: This phase blocks all user stories - must complete first.

- [X] T007 [P] Implement FitActivityParser class in src/openactivity/providers/garmin/fit_parser.py
- [X] T008 [P] Add sport type normalization in src/openactivity/providers/garmin/fit_parser.py
- [X] T009 Implement parse_fit_file convenience function in src/openactivity/providers/garmin/fit_parser.py

**Checkpoint**: FIT parsing ready - can now build import methods.

---

## Phase 4: User Story 1 - Import from Connected Device (Priority: P1) 🎯 MVP

**Goal**: Users can import activities from a USB-connected Garmin device.

**Independent Test**: Connect Garmin device via USB, run `openactivity garmin import --from-device`, verify activities appear in database.

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement find_connected_device() in src/openactivity/providers/garmin/importer.py
- [X] T011 [P] [US1] Implement import_from_device() in src/openactivity/providers/garmin/importer.py
- [X] T012 [US1] Create garmin import CLI command in src/openactivity/cli/garmin/import_cmd.py
- [X] T013 [US1] Add --from-device option to import command in src/openactivity/cli/garmin/import_cmd.py
- [X] T014 [US1] Register garmin command group in src/openactivity/cli/garmin/app.py
- [X] T015 [US1] Register garmin command group in src/openactivity/main.py

**Checkpoint**: User Story 1 fully functional - users can import from connected device.

---

## Phase 5: User Story 2 - Import from Garmin Connect Folder (Priority: P1)

**Goal**: Users can import activities from their local Garmin Connect folder (created by Garmin Express).

**Independent Test**: Sync device with Garmin Express, run `openactivity garmin import --from-connect`, verify activities appear.

### Implementation for User Story 2

- [X] T016 [P] [US2] Implement find_garmin_connect_directory() in src/openactivity/providers/garmin/importer.py
- [X] T017 [US2] Implement import_from_garmin_connect() in src/openactivity/providers/garmin/importer.py
- [X] T018 [US2] Add --from-connect option to import command in src/openactivity/cli/garmin/import_cmd.py

**Checkpoint**: User Story 2 fully functional - users can import from Garmin Connect folder.

---

## Phase 6: User Story 3 - Import from Bulk Export ZIP (Priority: P1)

**Goal**: Users can import their entire Garmin history from a bulk export ZIP file.

**Independent Test**: Download bulk export ZIP from Garmin, run `openactivity garmin import --from-zip PATH`, verify all activities imported.

### Implementation for User Story 3

- [X] T019 [P] [US3] Implement import_from_zip() in src/openactivity/providers/garmin/importer.py
- [X] T020 [US3] Add --from-zip option to import command in src/openactivity/cli/garmin/import_cmd.py

**Checkpoint**: User Story 3 fully functional - users can import from bulk export ZIP.

---

## Phase 7: User Story 4 - Import from Custom Directory (Priority: P2)

**Goal**: Users can import FIT files from any custom directory.

**Independent Test**: Place FIT files in custom folder, run `openactivity garmin import --from-directory PATH`, verify import.

### Implementation for User Story 4

- [X] T021 [P] [US4] Implement find_fit_files_in_directory() in src/openactivity/providers/garmin/importer.py
- [X] T022 [P] [US4] Implement import_from_directory() in src/openactivity/providers/garmin/importer.py
- [X] T023 [US4] Add --from-directory option to import command in src/openactivity/cli/garmin/import_cmd.py

**Checkpoint**: User Story 4 fully functional - users can import from custom directories.

---

## Phase 8: User Story 5 - Unified Activity Commands (Priority: P2)

**Goal**: Users can use provider-agnostic commands that work across both Strava and Garmin.

**Independent Test**: Import Garmin activities, run `openactivity activities list`, verify merged view with provider badges.

### Implementation for User Story 5

- [ ] T024 [P] [US5] Add provider badge helper function in src/openactivity/db/queries.py
- [ ] T025 [US5] Modify activities list command for multi-provider support in src/openactivity/cli/strava/activities.py
- [ ] T026 [US5] Add --provider filter option to activities list in src/openactivity/cli/strava/activities.py
- [ ] T027 [US5] Modify activity detail command for provider auto-detection in src/openactivity/cli/strava/activities.py
- [ ] T028 [US5] Add provider badge display in activity list output in src/openactivity/cli/strava/activities.py

**Checkpoint**: User Story 5 fully functional - unified commands work across providers.

---

## Phase 9: Testing & Quality Assurance

**Purpose**: Ensure robustness with comprehensive tests.

### Unit Tests

- [ ] T029 [P] Create unit tests for FIT parsing in tests/unit/test_fit_parser.py
- [ ] T030 [P] Create unit tests for import logic in tests/unit/test_garmin_import.py
- [ ] T031 [P] Create unit tests for device detection in tests/unit/test_device_detection.py

### Integration Tests

- [ ] T032 [P] Create end-to-end import test with sample FIT files in tests/integration/test_garmin_import_e2e.py
- [ ] T033 [P] Test import from device (mock mount point) in tests/integration/test_device_import.py
- [ ] T034 [P] Test import from ZIP in tests/integration/test_zip_import.py

### Test Fixtures

- [ ] T035 [P] Add sample FIT files to tests/fixtures/sample_activities/ (run, ride, swim)
- [ ] T036 [P] Add edge case FIT files (corrupted, non-activity, minimal data)

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Production readiness.

### Error Handling & UX

- [ ] T037 [P] Add comprehensive error messages to import command
- [ ] T038 [P] Add progress feedback for large imports (>100 files)
- [ ] T039 Validate all command help text consistency

### Performance

- [ ] T040 [P] Test import performance with 1000+ FIT files
- [ ] T041 [P] Optimize memory usage for large ZIP imports
- [ ] T042 Profile FIT parsing performance

### Cross-Platform Testing

- [ ] T043 Test device detection on Linux
- [ ] T044 Test device detection on macOS
- [ ] T045 Test device detection on Windows (if available)

### Documentation

- [ ] T046 [P] Update quickstart.md with FIT import examples
- [ ] T047 [P] Update research.md with API failure documentation
- [ ] T048 [P] Add troubleshooting guide for common import issues
- [ ] T049 Update README with Garmin setup instructions

### Linting & Code Quality

- [ ] T050 Run linting/formatting checks and fix issues
- [ ] T051 Run full test suite and fix any failures
- [ ] T052 Validate quickstart.md scenarios work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately ✅ COMPLETE
- **Foundational (Phase 2)**: Depends on Setup completion ✅ COMPLETE
- **Core FIT Parsing (Phase 3)**: Depends on Foundational - BLOCKS all user stories ✅ COMPLETE
- **User Story 1 (Phase 4)**: Depends on Core FIT Parsing ✅ COMPLETE
- **User Story 2 (Phase 5)**: Depends on Core FIT Parsing (no dependency on US1) ✅ COMPLETE
- **User Story 3 (Phase 6)**: Depends on Core FIT Parsing (no dependency on US1 or US2) ✅ COMPLETE
- **User Story 4 (Phase 7)**: Depends on Core FIT Parsing (no dependency on other stories) ✅ COMPLETE
- **User Story 5 (Phase 8)**: Depends on any user story completing (needs activities in database)
- **Testing (Phase 9)**: Can start after Core FIT Parsing complete
- **Polish (Phase 10)**: Depends on desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Core - import from device ✅ COMPLETE
- **User Story 2 (P1)**: Core - import from Garmin Connect folder ✅ COMPLETE
- **User Story 3 (P1)**: Core - import from bulk export ZIP ✅ COMPLETE
- **User Story 4 (P2)**: Nice to have - custom directory import ✅ COMPLETE
- **User Story 5 (P2)**: Enhances UX - unified commands

**Note**: User Stories 1-4 are completely independent after Phase 3. They can be implemented in parallel by different developers.

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup ✅
2. Complete Phase 2: Foundational ✅
3. Complete Phase 3: Core FIT Parsing ✅
4. Complete Phase 4: User Story 1 (Import from Device) ✅
5. Complete Phase 5: User Story 2 (Import from Connect Folder) ✅
6. Complete Phase 6: User Story 3 (Import from ZIP) ✅
7. **STOP and VALIDATE**: Test all import methods independently
8. Deploy/demo if ready - this provides complete import functionality

### Incremental Delivery

1. Setup + Foundational + Core FIT Parsing → FIT parsing ready ✅
2. Add US1 (Device Import) → Test independently → Can import from device ✅
3. Add US2 (Connect Import) → Test independently → Can import from Garmin Express ✅
4. Add US3 (ZIP Import) → Test independently → Can import bulk export (MVP!) ✅
5. Add US4 (Custom Dir) → Test independently → Flexible import options ✅
6. Add US5 (Unified Commands) → Test independently → Seamless multi-provider UX
7. Polish → Production ready

### Parallel Team Strategy

With multiple developers after Phase 3:

1. Team completes Setup + Foundational + Core FIT Parsing together ✅
2. Once Phase 3 done:
   - Developer A: User Story 1 (Device Import) ✅
   - Developer B: User Story 2 (Connect Import) ✅
   - Developer C: User Story 3 (ZIP Import) ✅
3. After US1-3 complete:
   - Developer A: User Story 4 (Custom Directory) ✅
   - Developer B: User Story 5 (Unified Commands)
   - Developer C: Testing (Phase 9)
4. Stories integrate independently

---

## Notes

- All tasks follow strict checklist format: `- [ ] [ID] [P?] [Story?] Description with file path`
- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Database migration (Phase 2) is blocking for all user stories
- Core FIT Parsing (Phase 3) is blocking for all import methods
- User Stories 1-4 are independent of each other (can parallelize)
- User Story 5 requires at least one import method working

**Total tasks**: 52 (down from 53 in API approach)
**MVP scope**: Phases 1-6 (Setup + Foundational + Core + US1 + US2 + US3) = 23 tasks ✅ COMPLETE
**Remaining**: Phases 8-10 (US5 + Testing + Polish) = 29 tasks
