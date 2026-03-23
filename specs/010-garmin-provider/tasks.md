# Tasks: Garmin Connect Provider

**Input**: Design documents from `/specs/010-garmin-provider/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Add dependencies and create directory structure

- [X] T001 Add garminconnect library to pyproject.toml dependencies
- [X] T002 Create provider directory structure at src/openactivity/providers/garmin/
- [X] T003 Create CLI directory structure at src/openactivity/cli/garmin/

---

## Phase 2: Foundational (Database Migration)

**Purpose**: Extend database schema for multi-provider support. MUST complete before ANY user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Add provider and provider_id fields to Activity model in src/openactivity/db/models.py
- [X] T005 [P] Create ActivityLink model in src/openactivity/db/models.py
- [X] T006 [P] Create GarminDailySummary model in src/openactivity/db/models.py
- [X] T007 [P] Create GarminSleepSession model in src/openactivity/db/models.py
- [X] T008 Create database migration script in src/openactivity/db/migrations/001_add_garmin_support.py
- [X] T009 Add migration execution to database initialization in src/openactivity/db/database.py

**Checkpoint**: Database schema ready - all user stories can now proceed in parallel.

---

## Phase 3: User Story 1 - Authenticate with Garmin Connect (Priority: P1) 🎯 MVP

**Goal**: Users can authenticate the CLI with their Garmin Connect credentials and credentials are stored securely in the system keyring.

**Independent Test**: Run `openactivity garmin auth`, provide credentials, verify success message and subsequent commands work without re-authentication.

### Tests for User Story 1

- [ ] T010 [P] [US1] Create unit tests for Garmin authentication in tests/unit/test_garmin_auth.py
- [ ] T011 [P] [US1] Create integration tests for keyring storage in tests/integration/test_garmin_auth.py

### Implementation for User Story 1

- [X] T012 [P] [US1] Create Garmin API client wrapper in src/openactivity/providers/garmin/client.py
- [X] T013 [US1] Implement Garmin authentication module in src/openactivity/providers/garmin/auth.py
- [X] T014 [US1] Extend keyring module to support Garmin credentials in src/openactivity/auth/keyring.py
- [X] T015 [US1] Create Garmin CLI command group in src/openactivity/cli/garmin/app.py
- [X] T016 [US1] Implement garmin auth command in src/openactivity/cli/garmin/auth.py
- [X] T017 [US1] Register Garmin command group in src/openactivity/main.py

**Checkpoint**: User Story 1 fully functional - users can authenticate with Garmin Connect.

---

## Phase 4: User Story 2 - Sync Garmin Activities (Priority: P1)

**Goal**: Users can sync their Garmin activities to local storage and duplicates are automatically detected and linked with Strava activities.

**Independent Test**: Run `openactivity garmin sync`, verify activities appear in database, run `openactivity activities list` and see merged view with provider badges.

### Tests for User Story 2

- [ ] T018 [P] [US2] Create unit tests for Garmin sync logic in tests/unit/test_garmin_sync.py
- [ ] T019 [P] [US2] Create unit tests for data transformation in tests/unit/test_garmin_transform.py
- [ ] T020 [P] [US2] Create unit tests for deduplication algorithm in tests/unit/test_deduplication.py
- [ ] T021 [P] [US2] Create integration tests for full sync workflow in tests/integration/test_garmin_sync.py

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement Garmin to local model transformation in src/openactivity/providers/garmin/transform.py
- [X] T023 [US2] Implement activity sync logic in src/openactivity/providers/garmin/sync.py
- [X] T024 [US2] Add deduplication detection function in src/openactivity/db/queries.py
- [X] T025 [US2] Add activity linking function in src/openactivity/db/queries.py
- [X] T026 [US2] Integrate deduplication into sync workflow in src/openactivity/providers/garmin/sync.py
- [X] T027 [US2] Implement garmin sync command in src/openactivity/cli/garmin/sync.py
- [X] T028 [US2] Add incremental sync support with sync state tracking in src/openactivity/providers/garmin/sync.py

**Checkpoint**: User Story 2 fully functional - users can sync Garmin activities and see merged view.

---

## Phase 5: User Story 3 - Sync Garmin Health Data (Priority: P2)

**Goal**: Users can sync daily health metrics (HRV, Body Battery, sleep, stress) from Garmin and view them via CLI.

**Independent Test**: Run `openactivity garmin sync`, then `openactivity garmin daily --last 7d` to see health metrics.

### Tests for User Story 3

- [ ] T029 [P] [US3] Create unit tests for health data sync in tests/unit/test_garmin_health.py
- [ ] T030 [P] [US3] Create unit tests for daily command in tests/unit/test_garmin_daily.py

### Implementation for User Story 3

- [ ] T031 [US3] Extend transform module for health data in src/openactivity/providers/garmin/transform.py
- [ ] T032 [US3] Add health data sync to sync module in src/openactivity/providers/garmin/sync.py
- [ ] T033 [US3] Add health data queries in src/openactivity/db/queries.py
- [ ] T034 [US3] Implement garmin daily command in src/openactivity/cli/garmin/daily.py
- [ ] T035 [US3] Add health data output formatting in src/openactivity/cli/garmin/daily.py

**Checkpoint**: User Story 3 fully functional - users can view Garmin health data.

---

## Phase 6: User Story 4 - Unified Activity Commands (Priority: P2)

**Goal**: Users can use `openactivity activity <ID>` and `openactivity activities list` commands that work across both Strava and Garmin providers.

**Independent Test**: Run `openactivity activities list` and see activities from both providers with badges. Run `openactivity activity <ID>` with any provider ID.

### Tests for User Story 4

- [ ] T036 [P] [US4] Create unit tests for provider-agnostic queries in tests/unit/test_provider_queries.py
- [ ] T037 [P] [US4] Create integration tests for unified commands in tests/integration/test_unified_commands.py

### Implementation for User Story 4

- [ ] T038 [P] [US4] Add provider-aware activity queries in src/openactivity/db/queries.py
- [ ] T039 [P] [US4] Add provider badge helper function in src/openactivity/db/queries.py
- [ ] T040 [US4] Modify activities list command for multi-provider support in src/openactivity/cli/strava/activities.py
- [ ] T041 [US4] Add --provider filter option to activities list in src/openactivity/cli/strava/activities.py
- [ ] T042 [US4] Modify activity detail command for auto-detection in src/openactivity/cli/strava/activities.py
- [ ] T043 [US4] Add provider badge display in activity list output in src/openactivity/cli/strava/activities.py

**Checkpoint**: User Story 4 fully functional - unified commands work across providers.

---

## Phase 7: User Story 5 - View Athlete Profile from Garmin (Priority: P3)

**Goal**: Users can view their Garmin Connect athlete profile information to verify account details.

**Independent Test**: Run `openactivity garmin athlete` and see profile information displayed.

### Tests for User Story 5

- [ ] T044 [P] [US5] Create unit tests for athlete profile in tests/unit/test_garmin_athlete.py

### Implementation for User Story 5

- [ ] T045 [US5] Add athlete profile fetching in src/openactivity/providers/garmin/client.py
- [ ] T046 [US5] Implement garmin athlete command in src/openactivity/cli/garmin/athlete.py

**Checkpoint**: User Story 5 fully functional - users can view Garmin profile.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T047 [P] Create Garmin activities list command in src/openactivity/cli/garmin/activities.py
- [ ] T048 [P] Add contract tests for Garmin provider interface in tests/contract/test_garmin_provider.py
- [ ] T049 Run full test suite and fix any failures
- [ ] T050 Run linting/formatting checks and fix issues
- [ ] T051 [P] Update README with Garmin setup instructions
- [ ] T052 [P] Add example workflows to documentation
- [ ] T053 Validate quickstart.md scenarios work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) and User Story 1 (auth required for sync)
- **User Story 3 (Phase 5)**: Depends on User Story 2 (health data syncs alongside activities)
- **User Story 4 (Phase 6)**: Depends on User Story 2 (needs synced activities to display)
- **User Story 5 (Phase 7)**: Depends on User Story 1 (auth required) - Independent of other stories
- **Polish (Phase 8)**: Depends on desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Core - can start after Foundational phase
- **User Story 2 (P1)**: Depends on US1 (auth needed for sync)
- **User Story 3 (P2)**: Extends US2 (health data is part of sync)
- **User Story 4 (P2)**: Depends on US2 (needs activities to display)
- **User Story 5 (P3)**: Only depends on US1 (just needs auth)

### Parallel Opportunities

**Phase 1 (Setup)**: All 3 tasks can run in parallel

**Phase 2 (Foundational)**:
- T005, T006, T007 can run in parallel (different models)

**Phase 3 (User Story 1)**:
- T010, T011 can run in parallel (different test files)
- T012 can run in parallel with others (different file)

**Phase 4 (User Story 2)**:
- T018, T019, T020, T021 can all run in parallel (different test files)
- T022 can run in parallel with others (different file)

**Phase 5 (User Story 3)**:
- T029, T030 can run in parallel (different test files)

**Phase 6 (User Story 4)**:
- T036, T037 can run in parallel (different test files)
- T038, T039 can run in parallel (different functions)

**Phase 7 (User Story 5)**:
- T044 can run in parallel with T045 (different files)

**Phase 8 (Polish)**:
- T047, T048, T051, T052 can all run in parallel (different files)

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Auth)
4. Complete Phase 4: User Story 2 (Activity Sync)
5. **STOP and VALIDATE**: Test auth + sync independently
6. Deploy/demo if ready - this provides core multi-provider functionality

### Incremental Delivery

1. Setup + Foundational → Database ready
2. Add US1 (Auth) → Test independently → Can authenticate
3. Add US2 (Activity Sync) → Test independently → Can sync activities (MVP!)
4. Add US3 (Health Data) → Test independently → Can view health metrics
5. Add US4 (Unified Commands) → Test independently → Seamless multi-provider UX
6. Add US5 (Athlete Profile) → Test independently → Profile viewing
7. Polish → Production ready

### Parallel Team Strategy

With multiple developers after Foundational phase:

1. Team completes Setup + Foundational together
2. Once Foundational done:
   - Developer A: User Story 1 (Auth)
   - Developer B: Prep for User Story 2 (write tests, plan transform logic)
3. After US1 complete:
   - Developer A: User Story 5 (Athlete Profile - only needs auth)
   - Developer B: User Story 2 (Activity Sync)
4. After US2 complete:
   - Developer A: User Story 3 (Health Data - extends sync)
   - Developer B: User Story 4 (Unified Commands)
5. Stories integrate independently

---

## Notes

- All tasks follow strict checklist format: `- [ ] [ID] [P?] [Story?] Description with file path`
- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are written first and should fail before implementation
- Database migration (Phase 2) is blocking for all user stories
- US1 (Auth) is blocking for US2, US3, US5 (all need authentication)
- US2 (Activity Sync) is blocking for US3 (health syncs with activities) and US4 (needs activities to display)
- US5 can start immediately after US1 (only needs auth, independent of other features)
- Total tasks: 53
- MVP scope: Phases 1-4 (Setup + Foundational + US1 + US2) = 28 tasks
