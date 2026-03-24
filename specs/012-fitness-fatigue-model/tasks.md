# Tasks: Fitness/Fatigue Model (ATL/CTL/TSB)

**Input**: Design documents from `/specs/012-fitness-fatigue-model/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested — test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new project setup needed — creates one new analysis module.

- [x] T001 Create src/openactivity/analysis/fitness.py with module docstring, imports, and constants (ATL_DAYS=7, CTL_DAYS=42, DEFAULT_MAX_HR=190, DEFAULT_REST_HR=60)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core TSS computation that all user stories depend on.

**CRITICAL**: TSS must be correct before ATL/CTL/TSB can be computed.

- [x] T002 Implement `estimate_max_hr(session)` in src/openactivity/analysis/fitness.py that returns the highest observed `max_heartrate` across all activities, falling back to DEFAULT_MAX_HR if none found
- [x] T003 Implement `compute_tss(activity, max_hr, rest_hr)` in src/openactivity/analysis/fitness.py using TRIMP formula: `duration_min * hr_ratio * 0.64 * exp(1.92 * hr_ratio)` where `hr_ratio = (avg_hr - rest_hr) / (max_hr - rest_hr)`. Return None if activity has no average_heartrate.
- [x] T004 Implement `compute_daily_tss(session, *, after, before, activity_type)` in src/openactivity/analysis/fitness.py that queries activities (using existing `get_activities` with dedup), computes TSS for each, and returns a dict of `{date: total_tss}` keyed by calendar date

**Checkpoint**: `compute_tss()` returns reasonable values: easy 30-min run ~30-50, hard 60-min tempo ~80-120.

---

## Phase 3: User Story 1 — View Current Fitness/Fatigue/Form (Priority: P1) MVP

**Goal**: User runs `openactivity strava analyze fitness` and sees today's CTL, ATL, TSB and a status label.

**Independent Test**: Run `openactivity strava analyze fitness` with 6 months of HR data. Verify CTL/ATL/TSB values and status label shown.

### Implementation for User Story 1

- [x] T005 [US1] Implement `compute_fitness_fatigue(daily_tss, *, num_days)` in src/openactivity/analysis/fitness.py that takes the daily TSS dict and runs the exponential decay forward, returning a list of `{date, tss, atl, ctl, tsb}` dicts for each day in the range
- [x] T006 [US1] Implement `classify_status(ctl_current, ctl_14d_ago, tsb_current)` in src/openactivity/analysis/fitness.py returning one of "peaking", "maintaining", "overreaching", "detraining" per research.md R6 thresholds
- [x] T007 [US1] Implement `analyze_fitness(session, *, last, activity_type)` orchestrator in src/openactivity/analysis/fitness.py that calls estimate_max_hr, compute_daily_tss, compute_fitness_fatigue, classify_status and returns a complete result dict matching the JSON contract in contracts/cli-commands.md
- [x] T008 [US1] Add `fitness` command to the analyze typer app in src/openactivity/cli/strava/analyze.py with options `--last` (str, default "6m"), `--type` (str, optional), `--chart` (bool), `--output` (str). Calls `analyze_fitness()` and displays rich output per contracts/cli-commands.md
- [x] T009 [US1] Implement rich terminal output for the fitness command in src/openactivity/cli/strava/analyze.py: status label with arrow, current CTL/ATL/TSB with 14-day change, metadata (activities counted, max HR, time range), and recent 14-day trend table

**Checkpoint**: `openactivity strava analyze fitness` shows current CTL/ATL/TSB with status label.

---

## Phase 4: User Story 2 — View Fitness Trend Over Time (Priority: P1)

**Goal**: User runs `openactivity strava analyze fitness --last 1y` and sees daily trend with direction.

**Independent Test**: Run with `--last 1y` and `--type Run` filter. Verify daily values shown and trend direction reported.

### Implementation for User Story 2

- [x] T010 [US2] Add `--last` time range parsing in the fitness command in src/openactivity/cli/strava/analyze.py: parse "30d", "90d", "6m", "1y", "all" into a start date. Pass to `analyze_fitness()`.
- [x] T011 [US2] Add `--type` activity filter in the fitness command in src/openactivity/cli/strava/analyze.py: pass to `analyze_fitness()` which passes to `compute_daily_tss()` query filter
- [x] T012 [US2] Implement `--json` output for the fitness command in src/openactivity/cli/strava/analyze.py returning the full JSON structure from contracts/cli-commands.md including the daily array

**Checkpoint**: `openactivity strava analyze fitness --last 1y --type Run --json` returns correct filtered data.

---

## Phase 5: User Story 3 — Visualize Fitness Chart (Priority: P2)

**Goal**: User runs `openactivity strava analyze fitness --chart` and gets a PNG chart.

**Independent Test**: Run with `--chart --output test.png`, verify PNG is created with 3 lines.

### Implementation for User Story 3

- [x] T013 [US3] Implement `generate_fitness_chart(daily_data, output_path)` in src/openactivity/analysis/fitness.py using matplotlib: plot CTL (blue), ATL (red), TSB (green dashed), horizontal line at TSB=0, legend, title, date x-axis
- [x] T014 [US3] Wire `--chart` and `--output` flags in the fitness command in src/openactivity/cli/strava/analyze.py to call `generate_fitness_chart()` after computing data, display success message with file path

**Checkpoint**: `openactivity strava analyze fitness --chart` generates a readable chart image.

---

## Phase 6: User Story 4 — Per-Activity TSS (Priority: P2)

**Goal**: Activity detail view shows TSS for activities with HR data.

**Independent Test**: Run `openactivity activity <ID>` for an activity with HR. Verify TSS is shown.

### Implementation for User Story 4

- [x] T015 [P] [US4] Add TSS display to the human-readable activity detail in src/openactivity/cli/strava/activities.py: import `compute_tss` and `estimate_max_hr`, compute TSS for the activity, display "TSS: X" after existing metrics (skip if no HR)
- [x] T016 [P] [US4] Add TSS to the JSON activity detail output in src/openactivity/cli/strava/activities.py: add `"tss"` field to the JSON dict

**Checkpoint**: `openactivity activity <ID>` shows TSS value for HR-equipped activities.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, edge cases, and end-to-end validation.

- [x] T017 Add error handling in the fitness command in src/openactivity/cli/strava/analyze.py for: no activities, no HR data, insufficient data (<7 days warning)
- [x] T018 Run `openactivity strava analyze fitness` against real database to validate end-to-end: check TSS values are reasonable, CTL/ATL/TSB make sense, status label is correct
- [x] T019 Run `openactivity strava analyze fitness --chart --output /tmp/fitness.png` to validate chart generation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies
- **Phase 2 (Foundational)**: Depends on Phase 1 (module must exist)
- **Phase 3 (US1)**: Depends on Phase 2 (TSS must work)
- **Phase 4 (US2)**: Depends on Phase 3 (fitness command must exist)
- **Phase 5 (US3)**: Depends on Phase 3 (needs computed data to chart)
- **Phase 6 (US4)**: Depends on Phase 2 only (just needs compute_tss)
- **Phase 7 (Polish)**: Depends on all user stories

### User Story Dependencies

- **US1 (Current Status)**: Can start after Phase 2
- **US2 (Trend Over Time)**: Depends on US1 (extends the same command)
- **US3 (Chart)**: Depends on US1 (needs the computed data)
- **US4 (Per-Activity TSS)**: Can start after Phase 2 — independent of US1 (different file)

### Parallel Opportunities

- US1 and US4 can run in parallel after Phase 2 (different files)
- T015 and T016 are marked [P] (both in activities.py but independent additions)
- US3 can start as soon as US1 is done

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Create module
2. Complete Phase 2: TSS computation
3. Complete Phase 3: Fitness command
4. **STOP and VALIDATE**: Run against real data
5. User can now see their fitness/fatigue/form

### Incremental Delivery

1. Phase 2 → TSS works → Foundation ready
2. Phase 3 (US1) → Current status → **MVP!**
3. Phase 4 (US2) → Time range + type filter + JSON → Full CLI
4. Phase 5 (US3) → Chart → Visual wow factor
5. Phase 6 (US4) → Per-activity TSS → Granularity
6. Phase 7 → Polish → Production-ready

---

## Notes

- No new dependencies required — matplotlib already in project
- No schema changes — all computed on-the-fly
- 1 new file (analysis/fitness.py), 2 modified files (analyze.py, activities.py)
- TRIMP formula from research.md R1 is the core algorithm
- Deduplication handled by existing get_activities() filter from Feature 011
