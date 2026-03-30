# Tasks: Unified Command Refactoring

**Input**: Design documents from `/specs/013-unified-command-refactor/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-commands.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new project structure needed — this is a refactoring of existing files.

- [x] T001 Add `provider` parameter to `get_activities()` in src/openactivity/db/queries.py — optional `str | None`, default `None`, filters by `Activity.provider` when set (ALREADY EXISTS)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core query-layer support for `--provider` filtering that all promoted commands depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Add `provider` parameter to `compute_pace_trend()` in src/openactivity/analysis/pace.py and pass through to `get_activities()`
- [x] T003 [P] Add `provider` parameter to analysis functions in src/openactivity/analysis/records.py (`scan_all_activities`, `scan_activity_for_records`) and pass through to activity queries
- [x] T004 [P] Add `provider` parameter to analysis functions in src/openactivity/analysis/compare.py and pass through to `get_activities()`
- [x] T005 [P] Add `provider` parameter to any remaining analysis modules that call `get_activities()` (blocks.py, correlate.py, power.py, effort scoring, drift, risk)

**Checkpoint**: All analysis modules accept an optional `provider` parameter and pass it to the query layer.

---

## Phase 3: User Story 1 — Promote Analyze Commands to Top Level (Priority: P1) 🎯 MVP

**Goal**: All `strava analyze` subcommands (summary, pace, zones, power-curve, compare, correlate, effort, blocks, drift, risk) available at `openactivity analyze` with `--provider` support.

**Independent Test**: Run `openactivity analyze pace` and verify it returns data from all providers. Run `openactivity analyze pace --provider garmin` and verify only Garmin data.

### Implementation for User Story 1

- [x] T006 [US1] Move analyze command functions from src/openactivity/cli/strava/analyze.py into src/openactivity/cli/analyze.py — add `--provider` option to each command, wire up provider parameter to analysis calls
- [x] T007 [US1] Register all analyze subcommands in the top-level analyze app in src/openactivity/cli/analyze.py (summary, pace, zones, power-curve, compare, correlate, effort, blocks, drift, risk)
- [x] T008 [US1] Convert src/openactivity/cli/strava/analyze.py to a thin alias — create a strava-specific analyze app that wraps the top-level analyze app with implicit `--provider strava`
- [x] T009 [US1] Update src/openactivity/cli/strava/app.py to register the alias analyze app instead of the old one
- [x] T010 [US1] Verify `openactivity analyze --help` shows all subcommands and `openactivity strava analyze --help` still works

**Checkpoint**: `openactivity analyze pace` works across all providers. `openactivity strava analyze pace` still works.

---

## Phase 4: User Story 2 — Promote Records Commands to Top Level (Priority: P1)

**Goal**: `records scan`, `records list`, `records history`, `records add-distance`, `records remove-distance` available at `openactivity records` with `--provider` support.

**Independent Test**: Run `openactivity records list` and verify PRs from all providers are shown.

### Implementation for User Story 2

- [x] T011 [P] [US2] Move records command functions from src/openactivity/cli/strava/records.py into new src/openactivity/cli/records.py — add `--provider` option to scan, list, and history commands
- [x] T012 [US2] Register the top-level records app in src/openactivity/main.py via `app.add_typer(records_app, name="records")`
- [x] T013 [US2] Convert src/openactivity/cli/strava/records.py to a thin alias that wraps the top-level records app with implicit `--provider strava`
- [x] T014 [US2] Update src/openactivity/cli/strava/app.py to register the alias records app

**Checkpoint**: `openactivity records list` works. `openactivity strava records list` still works.

---

## Phase 5: User Story 3 — Promote Predict Command to Top Level (Priority: P2)

**Goal**: `predict --distance` available at `openactivity predict` with `--provider` support.

**Independent Test**: Run `openactivity predict --distance 5K` and verify it uses data from all providers.

### Implementation for User Story 3

- [x] T015 [P] [US3] Move predict command from src/openactivity/cli/strava/predict.py into new src/openactivity/cli/predict.py — add `--provider` option
- [x] T016 [US3] Register the top-level predict app in src/openactivity/main.py
- [x] T017 [US3] Convert src/openactivity/cli/strava/predict.py to a thin alias wrapping the top-level predict app
- [x] T018 [US3] Update src/openactivity/cli/strava/app.py to register the alias predict app

**Checkpoint**: `openactivity predict --distance 5K` works. `openactivity strava predict` still works.

---

## Phase 6: User Story 4 — Promote Segments Commands to Top Level (Priority: P2)

**Goal**: `segments list` and `segment <ID> efforts|leaderboard|trend` available at the root level with `--provider` support.

**Independent Test**: Run `openactivity segments list` and verify segments are displayed.

### Implementation for User Story 4

- [x] T019 [P] [US4] Move segments/segment command functions from src/openactivity/cli/strava/segments.py into new src/openactivity/cli/segments.py — add `--provider` option where applicable
- [x] T020 [US4] Register the top-level segments and segment apps in src/openactivity/main.py
- [x] T021 [US4] Convert src/openactivity/cli/strava/segments.py to a thin alias wrapping the top-level apps
- [x] T022 [US4] Update src/openactivity/cli/strava/app.py to register the alias segments/segment apps

**Checkpoint**: `openactivity segments list` works. `openactivity strava segments list` still works.

---

## Phase 7: User Story 5 — Provider-Specific Commands Stay Namespaced (Priority: P1)

**Goal**: Verify `strava auth`, `strava sync`, `strava athlete`, `garmin import` remain under their namespaces and are NOT promoted.

**Independent Test**: Run `openactivity strava auth --help` and `openactivity garmin import --help` — both work. Verify no `openactivity auth` or `openactivity import` exists.

### Implementation for User Story 5

- [x] T023 [US5] Verify src/openactivity/main.py does NOT register auth, sync, athlete, or import at root level — no code changes expected, just validation
- [x] T024 [US5] Remove duplicate `strava activities` and `strava activity` from src/openactivity/cli/strava/app.py by aliasing them to the existing top-level versions (or leave as-is since they already share the same functions)

**Checkpoint**: Provider-specific commands only accessible under their namespaces.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Clean up, test, and validate the full command tree.

- [x] T025 [P] Add unit tests for top-level command routing in tests/unit/test_command_routing.py — verify all promoted commands resolve and --provider filter works
- [x] T026 [P] Update help text on all promoted commands to reference the new top-level paths in examples
- [x] T027 Run full test suite and verify no regressions
- [x] T028 Verify `openactivity --help` output shows promoted commands with clear descriptions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phases 3-6 (User Stories 1-4)**: All depend on Phase 2, can run in parallel with each other
- **Phase 7 (US5)**: No dependencies on other stories — mostly validation
- **Phase 8 (Polish)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Analyze)**: After Phase 2 — no dependencies on other stories
- **US2 (Records)**: After Phase 2 — no dependencies on other stories
- **US3 (Predict)**: After Phase 2 — no dependencies on other stories
- **US4 (Segments)**: After Phase 2 — no dependencies on other stories
- **US5 (Validation)**: Can run anytime — mostly verification

### Parallel Opportunities

- T002-T005 (analysis module updates) can all run in parallel
- T006 and T011 and T015 and T019 (moving command logic) can all run in parallel after Phase 2
- T025-T026 (tests and docs) can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Add `provider` to `get_activities()`
2. Complete Phase 2: Wire `provider` through analysis modules
3. Complete Phase 3: Promote analyze commands
4. **STOP and VALIDATE**: `openactivity analyze pace` works across providers
5. Ship if ready

### Incremental Delivery

1. Setup + Foundational → Query layer ready
2. Add US1 (Analyze) → Test → Ship (MVP!)
3. Add US2 (Records) → Test → Ship
4. Add US3 (Predict) + US4 (Segments) → Test → Ship
5. US5 (Validation) + Polish → Final ship

---

## Notes

- No new dependencies required
- No database schema changes
- Primary risk: ensuring backwards compatibility for all `strava` command paths
- The strava alias pattern should use the same Typer app instance registered at both levels, not duplicated code
- Commit after each phase checkpoint
