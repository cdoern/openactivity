# Tasks: Grade-Adjusted Pace & Effort Scoring

**Input**: Design documents from `/specs/005-gap-effort/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/cli-commands.md

**Tests**: Included — unit tests for GAP algorithm and effort scoring as specified in plan.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Create the analysis module file and establish constants

- [x] T001 Create `src/openactivity/analysis/gap.py` with Minetti energy cost model constants and cost function `C(g) = 155.4g^5 - 30.4g^4 - 43.3g^3 + 46.3g^2 + 19.5g + 3.6`, flat cost constant `C(0) = 3.6`, and grade smoothing window size constant (10)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core GAP computation logic that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Implement `compute_grades(altitude_stream, distance_stream)` function in `src/openactivity/analysis/gap.py` — computes grade (rise/run) between consecutive stream points with 10-point rolling average smoothing, returns list of smoothed grade values
- [x] T003 Implement `minetti_cost(grade)` function in `src/openactivity/analysis/gap.py` — applies the 5th-degree polynomial to a single grade value, returns energy cost in J/kg/m
- [x] T004 Implement `compute_gap(activity, session)` function in `src/openactivity/analysis/gap.py` — queries altitude and distance streams for an activity, calls `compute_grades` and `minetti_cost` per segment, computes distance-weighted average cost ratio, returns `GAPResult` dataclass with `overall_gap` (m/s), `lap_gaps` (list), `grade_profile`, and `available` flag. Returns `available=False` if streams missing.

**Checkpoint**: GAP computation core is ready — can compute GAP for any activity with stream data

---

## Phase 3: User Story 1 - View GAP for a Single Activity (Priority: P1) 🎯 MVP

**Goal**: Display overall and per-lap GAP alongside actual pace in the activity detail view

**Independent Test**: View a synced activity with elevation data and verify GAP values appear in output

### Tests for User Story 1

- [x] T005 [P] [US1] Create `tests/unit/test_gap.py` with tests for `compute_grades` — test flat terrain returns ~0 grades, uphill returns positive grades, downhill returns negative grades, smoothing reduces noise spikes
- [x] T006 [P] [US1] Add tests for `minetti_cost` in `tests/unit/test_gap.py` — test flat grade (0) returns 3.6, known uphill/downhill values match expected costs, symmetry check (uphill costs more than downhill of same magnitude)
- [x] T007 [P] [US1] Add tests for `compute_gap` in `tests/unit/test_gap.py` — test flat activity GAP ≈ actual pace, hilly activity GAP differs from actual pace, missing streams returns `available=False`, per-lap GAP values computed correctly

### Implementation for User Story 1

- [x] T008 [US1] Modify `show_activity()` in `src/openactivity/cli/strava/activities.py` — import and call `compute_gap`, add GAP line to summary section after existing Pace line (format: `GAP: X:XX /mi (grade-adjusted)`), show "GAP: unavailable" when `available=False`
- [x] T009 [US1] Modify laps table in `src/openactivity/cli/strava/activities.py` — add GAP column to the Rich table alongside existing Pace column, display per-lap GAP formatted as pace, show "—" for laps without GAP data

**Checkpoint**: User Story 1 is fully functional — `openactivity strava activity <ID>` shows GAP

---

## Phase 4: User Story 2 - Trend GAP Over Time (Priority: P2)

**Goal**: New `openactivity strava analyze effort` command showing GAP and effort across activities over time

**Independent Test**: Run the effort trend command and verify chronological activity list with GAP, trend direction, and summary stats

### Implementation for User Story 2

- [x] T010 [US2] Implement `parse_time_window(window_str)` helper in `src/openactivity/analysis/gap.py` — parse "30d", "90d", "6m", "1y", "all" into a datetime cutoff, return None for "all"
- [x] T011 [US2] Implement `compute_trend_direction(gap_values, dates)` in `src/openactivity/analysis/gap.py` — simple linear regression on GAP over time, classify as "improving" (slope < -2 sec/km/month), "declining" (slope > +2 sec/km/month), or "stable"
- [x] T012 [US2] Implement `get_effort_trend(session, time_window, activity_type)` in `src/openactivity/analysis/gap.py` — query activities filtered by type and date range, compute GAP for each, build list of `EffortTrendEntry` dicts and `EffortTrendSummary` with trend direction, avg GAP, avg effort score, activity count
- [x] T013 [US2] Add `effort` command to `src/openactivity/cli/strava/analyze.py` — typer command with `--last` (default "90d") and `--type` (default "Run") flags, calls `get_effort_trend`, renders Rich table with columns: Date, Activity, Distance, Pace, GAP, Elev., Effort. Show summary line below table with trend direction, avg GAP, avg effort. Handle empty results with informative message.

**Checkpoint**: User Story 2 functional — `openactivity strava analyze effort` shows trend table

---

## Phase 5: User Story 3 - Effort Score for Fair Comparison (Priority: P3)

**Goal**: Compute a normalized 0-100 effort score per activity accounting for duration, GAP, HR, and elevation

**Independent Test**: Verify harder efforts produce higher scores than easier efforts across varying terrain

### Tests for User Story 3

- [x] T014 [P] [US3] Add tests for `compute_effort_score` in `tests/unit/test_gap.py` — test score range 0-100, harder effort > easier effort, missing HR redistributes weights (33.3% each), very short easy run scores low (0-20), long hard hilly run scores high (75-100)

### Implementation for User Story 3

- [x] T015 [US3] Implement `compute_effort_score(activity, gap_result, all_activities_stats, session)` in `src/openactivity/analysis/gap.py` — 4-component percentile scoring: duration (25%), GAP speed (25%), HR as % of estimated max (25%), elevation gain per km (25%). When HR unavailable, redistribute to 33.3% each. Returns `EffortScoreResult` dataclass with score (int 0-100) and component breakdowns.
- [x] T016 [US3] Implement `get_user_activity_stats(session, activity_type)` in `src/openactivity/analysis/gap.py` — query all activities of given type to build percentile distributions for duration, GAP, and elevation gain per km. Returns stats dict used by effort score percentile computation.
- [x] T017 [US3] Wire effort score into `get_effort_trend` in `src/openactivity/analysis/gap.py` — call `compute_effort_score` for each activity in the trend, include score in `EffortTrendEntry`, compute avg in summary

**Checkpoint**: Effort scores appear in the effort trend table

---

## Phase 6: User Story 4 - JSON Output (Priority: P4)

**Goal**: All GAP and effort commands support structured JSON output for programmatic consumption

**Independent Test**: Run commands with `--json` flag and verify valid, parseable JSON with GAP and effort fields

### Implementation for User Story 4

- [x] T018 [P] [US4] Add JSON output for GAP in activity detail in `src/openactivity/cli/strava/activities.py` — add `gap`, `gap_formatted`, `gap_available` fields to JSON output dict, add per-lap `gap` and `gap_formatted` to lap entries. Use `null` when unavailable.
- [x] T019 [P] [US4] Add JSON output for effort trend in `src/openactivity/cli/strava/analyze.py` — when `--json` flag active, output JSON with `time_window`, `activity_type`, `trend`, `avg_gap`, `avg_gap_formatted`, `avg_effort_score`, `activity_count`, and `activities` array per contract spec

**Checkpoint**: All commands produce valid JSON with GAP and effort data

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validation, edge cases, and cleanup

- [x] T020 Run all tests with `pytest tests/unit/test_gap.py -v` and fix any failures
- [x] T021 Run `ruff check src/openactivity/analysis/gap.py src/openactivity/cli/strava/activities.py src/openactivity/cli/strava/analyze.py` and fix lint issues
- [x] T022 Manual validation: run `openactivity strava activity <ID>` on a real synced activity with elevation data and verify GAP display
- [x] T023 Manual validation: run `openactivity strava analyze effort` and verify trend table renders correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 completion
- **US2 (Phase 4)**: Depends on Phase 2 completion, can start in parallel with US1
- **US3 (Phase 5)**: Depends on Phase 2 completion, integrates with US2's trend output
- **US4 (Phase 6)**: Depends on US1 and US2 implementation being complete
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends only on Foundational (Phase 2) — fully independent
- **US2 (P2)**: Depends only on Foundational (Phase 2) — effort score initially placeholder until US3
- **US3 (P3)**: Depends on Phase 2, integrates into US2's trend command
- **US4 (P4)**: Depends on US1 and US2 having table output to add JSON alongside

### Within Each User Story

- Tests written and failing before implementation (where included)
- Core computation before CLI display
- Table output before JSON output

### Parallel Opportunities

- T005, T006, T007 (US1 tests) can run in parallel
- T018, T019 (US4 JSON) can run in parallel
- US1 and US2 implementation can proceed in parallel after Phase 2

---

## Parallel Example: User Story 1

```bash
# Launch all tests for US1 together:
Task: "Tests for compute_grades in tests/unit/test_gap.py"
Task: "Tests for minetti_cost in tests/unit/test_gap.py"
Task: "Tests for compute_gap in tests/unit/test_gap.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002-T004)
3. Complete Phase 3: User Story 1 (T005-T009)
4. **STOP and VALIDATE**: `openactivity strava activity <ID>` shows GAP
5. Continue to US2, US3, US4

### Incremental Delivery

1. Setup + Foundational → GAP computation core ready
2. Add US1 → GAP visible in activity detail (MVP!)
3. Add US2 → Effort trend command works
4. Add US3 → Effort scores computed and displayed
5. Add US4 → JSON output on all commands
6. Polish → Tests pass, lint clean, manual validation

---

## Notes

- No database schema changes — all computation is on-the-fly from existing stream data
- GAP uses Minetti energy cost model: `C(g) = 155.4g^5 - 30.4g^4 - 43.3g^3 + 46.3g^2 + 19.5g + 3.6`
- Effort score uses percentiles against user's own activity history
- Grade smoothing: 10-point rolling average on elevation-derived grades
- Trend detection: linear regression with ±2 sec/km/month threshold
- Activities with < 10 stream points excluded from GAP computation
