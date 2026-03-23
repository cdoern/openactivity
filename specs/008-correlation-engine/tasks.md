# Tasks: Cross-Activity Correlation Engine

**Input**: Design documents from `/specs/008-correlation-engine/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-commands.md

**Tests**: Included — unit tests for metric computation, correlation math, and lag analysis.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

## Phase 1: Setup

**Purpose**: Create the analysis module and install dependency

- [x] T001 Add `scipy` to project dependencies in `pyproject.toml` (or requirements file)
- [x] T002 Create `src/openactivity/analysis/correlate.py` with supported metrics registry (SUPPORTED_METRICS dict mapping metric names to descriptions), strength thresholds (WEAK=0.3, STRONG=0.7), minimum sample size constant (MIN_SAMPLES=4), and lag options list [0, 1, 2, 4]

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Weekly metric computation and correlation math

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Implement metric computation functions in `src/openactivity/analysis/correlate.py` — one function per metric: `_weekly_distance(week)`, `_weekly_duration(week)`, `_weekly_elevation(week)`, `_avg_pace(week)`, `_avg_hr(week)`, `_max_hr(week)`, `_activity_count(week)`, `_rest_days(week)`, `_longest_run(week)`. Each takes a WeekSummary dict (from aggregate_weeks) and returns float or None. Register in METRIC_FUNCTIONS dict.
- [x] T004 Implement `compute_weekly_metrics(session, activity_type, time_window)` in `src/openactivity/analysis/correlate.py` — query activities, call aggregate_weeks, extend each week with all metric values. Return list of WeeklyMetrics dicts.
- [x] T005 Implement `compute_correlation(x_values, y_values)` in `src/openactivity/analysis/correlate.py` — call scipy.stats.pearsonr and spearmanr, return dict with pearson_r, pearson_p, spearman_r, spearman_p. Handle constant arrays (zero variance) gracefully.
- [x] T006 Implement `classify_strength(r)` and `interpret_direction(x_metric, y_metric, r)` in `src/openactivity/analysis/correlate.py` — strength labels (weak/moderate/strong) and human-readable direction text.

**Checkpoint**: Core metric aggregation and correlation math complete

---

## Phase 3: User Story 1 - Correlate Two Metrics (Priority: P1) 🎯 MVP

**Goal**: Display Pearson and Spearman correlation between two weekly metrics

**Independent Test**: Run `openactivity strava analyze correlate --x weekly_distance --y avg_pace` and see correlation results

### Tests for User Story 1

- [x] T007 [P] [US1] Create `tests/unit/test_correlate.py` with tests for metric functions — test each metric returns correct value from mock week data, test avg_hr returns None when no HR data, test rest_days computation
- [x] T008 [P] [US1] Add tests for `compute_correlation` in `tests/unit/test_correlate.py` — test perfect positive correlation (r=1), perfect negative (r=-1), no correlation (~0), constant array returns error dict
- [x] T009 [P] [US1] Add tests for `classify_strength` and `interpret_direction` in `tests/unit/test_correlate.py` — test weak/moderate/strong thresholds, direction text for positive and negative correlations

### Implementation for User Story 1

- [x] T010 [US1] Implement `correlate(session, x_metric, y_metric, time_window, activity_type, lag)` orchestrator in `src/openactivity/analysis/correlate.py` — validate metric names, compute weekly metrics, extract paired values (excluding None), validate sample size ≥ 4, call compute_correlation, build CorrelationResult dict. Handle errors.
- [x] T011 [US1] Add `correlate` command to `src/openactivity/cli/strava/analyze.py` — typer command with `--x` (required), `--y` (required), `--last` (default "1y"), `--type` (default "Run") flags. Call correlate orchestrator, render Rich output: Pearson/Spearman results, strength, direction, sample size, data points table (first 10). Handle errors with informative messages.

**Checkpoint**: US1 complete — `openactivity strava analyze correlate --x weekly_distance --y avg_pace` shows correlation

---

## Phase 4: User Story 2 - Lag Analysis (Priority: P2)

**Goal**: Support `--lag` flag to offset Y-metric data for delayed-effect analysis

**Independent Test**: Run with `--lag 4` and verify lagged correlation

### Implementation for User Story 2

- [x] T012 [US2] Add `--lag` flag to correlate CLI command in `src/openactivity/cli/strava/analyze.py` — accepts int values 0, 1, 2, 4 (default 0). Pass to orchestrator.
- [x] T013 [US2] Implement lag offset in `correlate()` orchestrator in `src/openactivity/analysis/correlate.py` — when lag > 0, pair X[i] with Y[i+lag]. Validate that sample_size - lag >= MIN_SAMPLES. Show lag value in output.
- [x] T014 [P] [US2] Add lag tests in `tests/unit/test_correlate.py` — test lag=0 same as no lag, lag=4 correctly offsets data, lag exceeding data returns error

**Checkpoint**: US2 complete — lag analysis works

---

## Phase 5: User Story 3 - JSON Output (Priority: P3)

**Goal**: Structured JSON output for agent consumption

**Independent Test**: Run with `--json` flag and verify valid JSON

### Implementation for User Story 3

- [x] T015 [US3] Add JSON output to correlate command in `src/openactivity/cli/strava/analyze.py` — when `--json` flag active, output JSON with all fields per contract spec: pearson_r, pearson_p, spearman_r, spearman_p, strength, direction, significant, sample_size, total_weeks, lag, data_points array. Handle errors with error JSON.

**Checkpoint**: US3 complete — valid JSON output

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validation, testing, and cleanup

- [x] T016 Run all tests with `pytest tests/unit/test_correlate.py -v` and fix any failures
- [x] T017 Run `ruff check src/openactivity/analysis/correlate.py src/openactivity/cli/strava/analyze.py` and fix lint issues
- [x] T018 Run full test suite `pytest tests/ -v` and ensure no regressions
- [x] T019 Manual validation: run `openactivity strava analyze correlate --x weekly_distance --y avg_pace` on real data
- [x] T020 Manual validation: run with `--lag 4` and verify lagged results
- [x] T021 Manual validation: run `openactivity --json strava analyze correlate --x weekly_distance --y avg_pace` and verify JSON

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2
- **US2 (Phase 4)**: Depends on US1 (adds lag to existing command)
- **US3 (Phase 5)**: Depends on US1 (adds JSON output)
- **Polish (Phase 6)**: Depends on all user stories

### Parallel Opportunities

- T007, T008, T009 (US1 tests) can run in parallel
- US2 and US3 can proceed in parallel after US1

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T006)
3. Complete Phase 3: User Story 1 (T007-T011)
4. **STOP and VALIDATE**: `openactivity strava analyze correlate --x weekly_distance --y avg_pace` shows correlation
5. Continue to US2, US3

### Incremental Delivery

1. Setup + Foundational → Metric aggregation and correlation math ready
2. Add US1 → Correlation visible (MVP!)
3. Add US2 → Lag analysis
4. Add US3 → JSON output for agents
5. Polish → Tests pass, lint clean, manual validation

---

## Notes

- No database schema changes — all computation on-the-fly
- New dependency: scipy (for pearsonr, spearmanr with p-values)
- 9 supported metrics, extensible via METRIC_FUNCTIONS registry
- Lag: X[i] paired with Y[i+lag] — "does X predict Y in N weeks?"
- Strength: weak (|r| < 0.3), moderate (0.3-0.7), strong (≥ 0.7)
- Significance: p < 0.05
- Minimum 4 data points, warns below 12
- Reuses: blocks.py (aggregate_weeks), queries.py (get_activities)
