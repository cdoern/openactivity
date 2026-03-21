# Tasks: Custom Time-Range Comparisons

**Input**: Design documents from `/specs/003-time-range-compare/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — the existing project has a testing convention (pytest) and the constitution mandates tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: No new project setup needed — this feature adds to an existing codebase. This phase creates the new files.

- [x] T001 Create comparison analysis module at src/openactivity/analysis/compare.py with RangeMetrics and RangeComparison dataclasses
- [x] T002 Create unit test file at tests/unit/test_compare.py with test structure

**Checkpoint**: New files created, ready for implementation.

---

## Phase 2: Foundational (Date Parsing & Validation)

**Purpose**: Core date range parsing and validation logic that all user stories depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 Implement date range parsing function in src/openactivity/analysis/compare.py — accept `YYYY-MM-DD:YYYY-MM-DD` string, return (start_date, end_date) tuple, raise ValueError on invalid format or start > end
- [x] T004 Implement overlap detection function in src/openactivity/analysis/compare.py — accept two (start, end) tuples, return bool indicating whether ranges share any dates
- [x] T005 [P] Write unit tests for date parsing and validation in tests/unit/test_compare.py — valid formats, invalid formats, start > end, single-day ranges

**Checkpoint**: Date parsing and validation tested and working.

---

## Phase 3: User Story 1 - Compare Two Training Periods (Priority: P1) MVP

**Goal**: Users can compare aggregated training metrics across two arbitrary date ranges and see a side-by-side table with deltas and percentage changes.

**Independent Test**: Run `openactivity strava analyze compare --range1 2025-01-01:2025-03-31 --range2 2026-01-01:2026-03-31` and verify the output table shows correct metrics, deltas, and percentage changes.

### Implementation for User Story 1

- [x] T006 [US1] Implement `aggregate_range_metrics()` function in src/openactivity/analysis/compare.py — query activities via `get_activities()` with after/before filters, compute count, total distance, total moving time, total elevation gain, avg pace (foot-based types), avg speed (cycling), avg HR (when available), return RangeMetrics dataclass
- [x] T007 [US1] Implement `compute_comparison()` function in src/openactivity/analysis/compare.py — accept two RangeMetrics, compute deltas (range2 - range1) and percentage changes (handle zero-division as None), return RangeComparison dataclass
- [x] T008 [US1] Implement `format_pct_change()` helper in src/openactivity/analysis/compare.py — format percentage as "+21.4%" or "-4.5%", return "N/A" when range1 is zero, return "—" when both are zero
- [x] T009 [US1] Add `compare` command to src/openactivity/cli/strava/analyze.py — register with `@app.command("compare")`, add `--range1` (required), `--range2` (required) flags as strings, call parse/validate/aggregate/compare pipeline
- [x] T010 [US1] Implement Rich table output in src/openactivity/cli/strava/analyze.py compare command — build table with columns Metric, Range 1, Range 2, Delta, Change %; format values using existing `format_distance`, `format_duration`, `format_elevation` from output/units.py; add direction indicators (+/- and arrows); show range metadata and overlap warning below table
- [x] T011 [US1] Write unit tests for `aggregate_range_metrics()` in tests/unit/test_compare.py — test with activities in both ranges, one empty range, both empty ranges, activities with and without HR data
- [x] T012 [US1] Write unit tests for `compute_comparison()` in tests/unit/test_compare.py — verify delta calculations, percentage change accuracy, zero-division handling

**Checkpoint**: Core comparison works end-to-end with table output. User Story 1 is fully functional.

---

## Phase 4: User Story 2 - Filter by Activity Type (Priority: P2)

**Goal**: Users can filter the comparison to a specific activity type so mixed-sport metrics don't muddle results.

**Independent Test**: Run `openactivity strava analyze compare --range1 ... --range2 ... --type Run` and verify only running activities are included.

### Implementation for User Story 2

- [x] T013 [US2] Add `--type` optional flag to compare command in src/openactivity/cli/strava/analyze.py — pass activity_type to `aggregate_range_metrics()` calls, which forwards to `get_activities()` existing `activity_type` parameter
- [x] T014 [US2] Handle no-results case in src/openactivity/cli/strava/analyze.py compare command — when both ranges return zero activities with type filter, display informational message "No [type] activities found in either range" instead of a table of zeroes
- [x] T015 [US2] Write unit test for type-filtered comparison in tests/unit/test_compare.py — verify only matching activity types are included in aggregation

**Checkpoint**: Type filtering works. User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - JSON Output (Priority: P3)

**Goal**: Agents and scripts can consume comparison data as structured JSON.

**Independent Test**: Run `openactivity strava analyze compare --range1 ... --range2 ... --json` and verify output is valid JSON with all metrics, deltas, percentages, and metadata.

### Implementation for User Story 3

- [x] T016 [US3] Add JSON output branch to compare command in src/openactivity/cli/strava/analyze.py — when global `--json` flag is set, call `print_json()` with dict containing metadata (ranges, type filter, units, overlap), range1 metrics, range2 metrics, deltas, and pct_changes per the contract schema
- [x] T017 [US3] Implement `comparison_to_dict()` helper in src/openactivity/analysis/compare.py — serialize RangeComparison to dict matching the JSON schema defined in contracts/cli-commands.md, using raw metric units (meters, seconds) for machine consumption
- [x] T018 [US3] Write unit test for JSON serialization in tests/unit/test_compare.py — verify dict structure matches contract schema, verify None percentage changes serialize correctly

**Checkpoint**: All three user stories complete and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [x] T019 Add help text with usage examples to compare command in src/openactivity/cli/strava/analyze.py — include examples for basic comparison, type filter, and JSON output
- [x] T020 Update analyze command group help text in src/openactivity/cli/strava/analyze.py to list the new compare subcommand in the examples section
- [x] T021 Run quickstart.md validation — skipped (requires live synced data; CLI module imports and tests pass)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — core comparison logic
- **US2 (Phase 4)**: Depends on US1 (adds flag to existing command)
- **US3 (Phase 5)**: Depends on US1 (serializes existing comparison result)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 command existing (adds `--type` flag to it)
- **User Story 3 (P3)**: Depends on US1 comparison result existing (serializes it to JSON)

### Within Each User Story

- Implementation before tests (tests validate the implementation)
- Core logic (analysis module) before CLI wiring
- CLI wiring before output formatting

### Parallel Opportunities

- T001 and T002 can run in parallel (different files)
- T004 and T005 can run in parallel (different files)
- T011 and T012 can run in parallel (different test functions, same file but independent)
- US2 and US3 can run in parallel after US1 completes (independent additions)

---

## Parallel Example: User Story 1

```bash
# Core logic tasks (sequential — T007 depends on T006):
Task T006: "Implement aggregate_range_metrics() in src/openactivity/analysis/compare.py"
Task T007: "Implement compute_comparison() in src/openactivity/analysis/compare.py"
Task T008: "Implement format_pct_change() in src/openactivity/analysis/compare.py"

# Then CLI wiring:
Task T009: "Add compare command to src/openactivity/cli/strava/analyze.py"
Task T010: "Implement Rich table output in compare command"

# Then tests in parallel:
Task T011: "Unit tests for aggregate_range_metrics()"
Task T012: "Unit tests for compute_comparison()"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T005)
3. Complete Phase 3: User Story 1 (T006-T012)
4. **STOP and VALIDATE**: Run compare command with real synced data
5. Feature is usable at this point

### Incremental Delivery

1. Setup + Foundational → Date parsing works
2. Add User Story 1 → Table comparison works (MVP!)
3. Add User Story 2 → Type filtering works
4. Add User Story 3 → JSON output works
5. Polish → Help text and validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This feature touches only 2 source files (1 new, 1 modified) + 1 test file
- No database migrations or schema changes required
- Commit after each phase completion
