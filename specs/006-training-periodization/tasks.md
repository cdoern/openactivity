# Tasks: Training Block / Periodization Detector

**Input**: Design documents from `/specs/006-training-periodization/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-commands.md

**Tests**: Included — unit tests for classification algorithm and block grouping as specified in plan.md.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

## Phase 1: Setup

**Purpose**: Create the analysis module file and establish constants

- [x] T001 Create `src/openactivity/analysis/blocks.py` with phase classification constants (RECOVERY, BASE, BUILD, PEAK), volume threshold (0.70), intensity thresholds (60, 70), gap threshold (14 days), and minimum weeks constant (4)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core weekly aggregation and classification logic

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Implement `aggregate_weeks(activities, time_window)` in `src/openactivity/analysis/blocks.py` — group activities into ISO weeks (Mon-Sun), compute per-week total distance, total duration, activity count. Return list of WeekSummary dicts sorted chronologically.
- [x] T003 Implement `compute_week_intensity(week_activities, estimated_max_hr, pace_distribution)` in `src/openactivity/analysis/blocks.py` — compute normalized intensity (0-100) using avg HR as % of max HR when available, falling back to pace percentile rank. Return score and source ("hr", "pace", or "default").
- [x] T004 Implement `classify_weeks(weeks)` in `src/openactivity/analysis/blocks.py` — apply 4-week rolling average volume comparison and intensity thresholds to classify each week as recovery/base/build/peak per research.md rules. Handle first 3 weeks with absolute thresholds.
- [x] T005 Implement `group_into_blocks(weeks)` in `src/openactivity/analysis/blocks.py` — group consecutive weeks with same classification into TrainingBlock dicts. Force block boundary on gaps >14 days. Mark the last block as `is_current=True`. Return list of blocks.

**Checkpoint**: Core algorithm complete — can classify weeks and group into blocks

---

## Phase 3: User Story 1 - View Training Block Timeline (Priority: P1) 🎯 MVP

**Goal**: Display a timeline of detected training blocks with phase, date ranges, and metrics

**Independent Test**: Run `openactivity strava analyze blocks` and see a table of training blocks

### Tests for User Story 1

- [x] T006 [P] [US1] Create `tests/unit/test_blocks.py` with tests for `aggregate_weeks` — test activities grouped by ISO week, empty activities returns empty, single week aggregation, multi-week aggregation
- [x] T007 [P] [US1] Add tests for `classify_weeks` in `tests/unit/test_blocks.py` — test recovery detection (volume <70% of rolling avg), base detection (high volume, low intensity), build detection (rising volume + intensity), peak detection (high intensity, tapering volume)
- [x] T008 [P] [US1] Add tests for `group_into_blocks` in `tests/unit/test_blocks.py` — test consecutive same-phase weeks grouped, phase changes create new blocks, gap >14 days forces boundary, last block marked as current

### Implementation for User Story 1

- [x] T009 [US1] Implement `detect_blocks(session, time_window, activity_type)` in `src/openactivity/analysis/blocks.py` — orchestrate: query activities, aggregate weeks, compute intensity, classify weeks, group blocks. Return BlocksResult dict. Handle <4 weeks with error result.
- [x] T010 [US1] Add `blocks` command to `src/openactivity/cli/strava/analyze.py` — typer command with `--last` (default "6m") and `--type` (default "Run") flags. Call `detect_blocks`, render Rich table with columns: Phase, Start, End, Weeks, Avg Vol., Activities, Intensity. Mark current block with ◀. Show summary line with current phase, total weeks, total activities. Handle insufficient data with informative message.

**Checkpoint**: US1 complete — `openactivity strava analyze blocks` shows block timeline

---

## Phase 4: User Story 2 - Filter by Time Window and Activity Type (Priority: P2)

**Goal**: Support `--last` and `--type` flags for filtering

**Independent Test**: Run with different flags and verify results change

### Implementation for User Story 2

- [x] T011 [US2] Verify `--last` flag in `src/openactivity/cli/strava/analyze.py` supports "6m", "1y", "all" by reusing existing `_parse_time_window` pattern from gap.py. Add validation for unsupported values.
- [x] T012 [US2] Verify `--type` flag filters activities correctly using wildcard matching (already fixed in queries.py). Test with `--type Ride` to confirm cycling blocks work.

**Checkpoint**: US2 complete — filtering works for different sports and time ranges

---

## Phase 5: User Story 3 - Current Phase Identification (Priority: P3)

**Goal**: Highlight current phase with contextual meaning

**Independent Test**: Verify current block is clearly indicated with phase meaning

### Implementation for User Story 3

- [x] T013 [US3] Add phase descriptions to `src/openactivity/analysis/blocks.py` — dict mapping phase names to brief contextual descriptions (e.g., "Build: Rising volume and intensity — preparing for performance"). Include in BlocksResult.
- [x] T014 [US3] Enhance blocks table output in `src/openactivity/cli/strava/analyze.py` — add a "Current Phase" section below the table showing the phase name and its description/guidance.

**Checkpoint**: US3 complete — current phase clearly shown with context

---

## Phase 6: User Story 4 - JSON Output (Priority: P4)

**Goal**: Structured JSON output for agent consumption

**Independent Test**: Run with `--json` flag and verify valid parseable JSON

### Implementation for User Story 4

- [x] T015 [US4] Add JSON output for blocks in `src/openactivity/cli/strava/analyze.py` — when `--json` flag active, output JSON with `time_window`, `activity_type`, `current_phase`, `total_weeks`, and `blocks` array per contract spec. Include `avg_weekly_distance_formatted` per block. Handle insufficient data with error JSON.

**Checkpoint**: US4 complete — valid JSON with all block data

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validation, testing, and cleanup

- [x] T016 Run all tests with `pytest tests/unit/test_blocks.py -v` and fix any failures
- [x] T017 Run `ruff check src/openactivity/analysis/blocks.py src/openactivity/cli/strava/analyze.py` and fix lint issues
- [x] T018 Manual validation: run `openactivity strava analyze blocks` on real synced data and verify block timeline
- [x] T019 Manual validation: run `openactivity --json strava analyze blocks` and verify JSON output

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2
- **US2 (Phase 4)**: Depends on US1 (flags are part of the command)
- **US3 (Phase 5)**: Depends on US1 (enhances existing output)
- **US4 (Phase 6)**: Depends on US1 (adds JSON alongside table)
- **Polish (Phase 7)**: Depends on all user stories

### Parallel Opportunities

- T006, T007, T008 (US1 tests) can run in parallel
- US3 and US4 can proceed in parallel after US1

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002-T005)
3. Complete Phase 3: User Story 1 (T006-T010)
4. **STOP and VALIDATE**: `openactivity strava analyze blocks` shows blocks
5. Continue to US2, US3, US4

### Incremental Delivery

1. Setup + Foundational → classification algorithm ready
2. Add US1 → Block timeline visible (MVP!)
3. Add US2 → Filtering verified
4. Add US3 → Current phase highlighted with context
5. Add US4 → JSON output for agents
6. Polish → Tests pass, lint clean, manual validation

---

## Notes

- No database schema changes — all computation on-the-fly from activity-level metrics
- ISO week boundaries (Monday-Sunday)
- 4-week rolling average for volume baseline
- Classification: recovery (<70% vol), base (high vol, low intensity), build (rising vol+intensity), peak (high intensity, tapering vol)
- Gaps >14 days force block boundaries
- Minimum 4 weeks of data required
