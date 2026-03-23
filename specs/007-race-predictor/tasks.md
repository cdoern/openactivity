# Tasks: Race Predictor & Readiness Score

**Input**: Design documents from `/specs/007-race-predictor/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-commands.md

**Tests**: Included — unit tests for Riegel formula, readiness scoring, and edge cases.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

## Phase 1: Setup

**Purpose**: Create the analysis module file and establish constants

- [x] T001 Create `src/openactivity/analysis/predict.py` with distance constants (DISTANCES dict mapping labels to meters: 1mi=1609.34, 5K=5000, 10K=10000, half=21097.5, marathon=42195), Riegel exponent constant (1.06), readiness weight constants (CONSISTENCY_WEIGHT=0.30, VOLUME_WEIGHT=0.25, TAPER_WEIGHT=0.25, RECENCY_WEIGHT=0.20), readiness label thresholds, and confidence interval base percentage (0.02)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Riegel prediction and reference effort gathering logic

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Implement `get_reference_efforts(session, activity_type, max_age_days)` in `src/openactivity/analysis/predict.py` — query PersonalRecord table for current best efforts at standard distances (1mi, 5K, 10K, half, marathon), filter by activity type and recency, return list of ReferenceEffort dicts with distance_meters, time_seconds, activity_date, days_ago, distance_label. Fall back to scanning recent activities on-the-fly if no PR records exist.
- [x] T003 Implement `riegel_predict(reference_time, reference_distance, target_distance, exponent)` in `src/openactivity/analysis/predict.py` — pure function applying `T2 = T1 * (D2/D1)^exponent`. Return predicted time in seconds.
- [x] T004 Implement `predict_race_time(reference_efforts, target_distance_meters)` in `src/openactivity/analysis/predict.py` — apply Riegel formula from each reference effort to the target distance, compute weighted average (weight by recency and distance proximity to target), return Prediction dict with predicted_time, predicted_pace, confidence_low, confidence_high, confidence_pct, reference_efforts, prediction_source.
- [x] T005 Implement `compute_confidence_interval(predictions_from_refs, reference_efforts)` in `src/openactivity/analysis/predict.py` — base ±2% of predicted time, widen by: +1% per reference effort fewer than 4, +1% if oldest effort >90 days, +spread% if predictions from different references disagree. Return (low_seconds, high_seconds, pct).

**Checkpoint**: Core prediction algorithm complete — can predict race times from reference efforts

---

## Phase 3: User Story 1 - Predict Race Time (Priority: P1) 🎯 MVP

**Goal**: Display a predicted finish time for a target distance with confidence range

**Independent Test**: Run `openactivity strava predict --distance 10K` and see predicted time, pace, and confidence interval

### Tests for User Story 1

- [x] T006 [P] [US1] Create `tests/unit/test_predict.py` with tests for `riegel_predict` — test 5K→10K prediction, 10K→marathon prediction, identity (same distance returns same time), shorter distance returns faster time
- [x] T007 [P] [US1] Add tests for `predict_race_time` in `tests/unit/test_predict.py` — test single reference effort prediction, multiple reference weighted average, no reference efforts returns error dict
- [x] T008 [P] [US1] Add tests for `compute_confidence_interval` in `tests/unit/test_predict.py` — test baseline ±2%, widens with fewer references, widens with old data, narrows with 4+ recent efforts

### Implementation for User Story 1

- [x] T009 [US1] Implement `predict(session, target_distance, activity_type)` orchestrator in `src/openactivity/analysis/predict.py` — gather reference efforts, validate ≥2 available (or 1 with warning), call predict_race_time, return PredictResult dict. Handle insufficient data with error result.
- [x] T010 [US1] Create `src/openactivity/cli/strava/predict.py` — typer app with `race` command (default command), `--distance` flag (required, choices: 1mi/5K/10K/half/marathon), `--type` flag (default "Run"). Call `predict()`, render Rich output: predicted time, pace, confidence range, reference efforts table. Handle insufficient data with informative message.
- [x] T011 [US1] Register predict command in `src/openactivity/cli/strava/app.py` — import predict app and add as typer subcommand

**Checkpoint**: US1 complete — `openactivity strava predict --distance 10K` shows race prediction

---

## Phase 4: User Story 2 - Readiness Score (Priority: P2)

**Goal**: Show a readiness score (0-100) with 4-component breakdown alongside the prediction

**Independent Test**: Run `predict --distance half` and verify readiness score with labeled components

### Tests for User Story 2

- [x] T012 [P] [US2] Add tests for readiness components in `tests/unit/test_predict.py` — test consistency scoring (8/8 weeks=100, 4/8=50, 0/8=0), volume trend (increasing=high, decreasing=varies), taper detection (declining volume + stable intensity = high), PR recency (recent=high, old=low)
- [x] T013 [P] [US2] Add tests for `compute_readiness_score` in `tests/unit/test_predict.py` — test overall weighted calculation, label assignment (0-40 Not Ready, 41-60 Building, 61-80 Almost Ready, 81-100 Race Ready), missing data graceful handling

### Implementation for User Story 2

- [x] T014 [US2] Implement `compute_consistency(session, activity_type, weeks)` in `src/openactivity/analysis/predict.py` — use aggregate_weeks from blocks.py to get last 8 weeks, count weeks with ≥3 activities, return score 0-100 and description string.
- [x] T015 [US2] Implement `compute_volume_trend(session, activity_type)` in `src/openactivity/analysis/predict.py` — use aggregate_weeks to get last 8 weeks, compare last-4 vs prior-4 total distance, score: maintained/increasing volume scores high, sharp drops score low. Return score 0-100 and description.
- [x] T016 [US2] Implement `compute_taper_status(session, activity_type)` in `src/openactivity/analysis/predict.py` — use aggregate_weeks + compute_week_intensity for last 3 weeks, detect if volume decreasing while intensity maintained (±10%). Score high if tapering correctly, medium if flat, low if volume increasing. Return score 0-100 and description.
- [x] T017 [US2] Implement `compute_pr_recency(reference_efforts)` in `src/openactivity/analysis/predict.py` — find most recent reference effort, score based on days_ago: <14d=100, <30d=85, <60d=70, <90d=55, <180d=40, >180d=20. Return score 0-100 and description.
- [x] T018 [US2] Implement `compute_readiness_score(consistency, volume_trend, taper_status, pr_recency)` in `src/openactivity/analysis/predict.py` — weighted composite (30/25/25/20), assign label, return ReadinessScore dict with overall, label, and components.
- [x] T019 [US2] Enhance `predict()` orchestrator in `src/openactivity/analysis/predict.py` to include readiness score in PredictResult. Handle <4 weeks training data by showing prediction without readiness.
- [x] T020 [US2] Enhance predict CLI output in `src/openactivity/cli/strava/predict.py` — add readiness section below prediction: overall score, label, 4 bar-chart components with scores and descriptions. Show "insufficient training history" when <4 weeks.

**Checkpoint**: US2 complete — readiness score shown with breakdown

---

## Phase 5: User Story 3 - Race-Date Context (Priority: P3)

**Goal**: Add `--race-date` flag with days-until-race and training phase context

**Independent Test**: Run `predict --distance marathon --race-date 2026-06-15` and verify temporal context shown

### Implementation for User Story 3

- [x] T021 [US3] Add `--race-date` flag to predict CLI command in `src/openactivity/cli/strava/predict.py` — optional string, validate YYYY-MM-DD format and must be in the future. Pass to predict orchestrator.
- [x] T022 [US3] Enhance `predict()` orchestrator in `src/openactivity/analysis/predict.py` to accept race_date parameter — compute days_until_race, get current_phase from detect_blocks, add race context to PredictResult.
- [x] T023 [US3] Enhance predict CLI output in `src/openactivity/cli/strava/predict.py` — when race_date provided, show "Race Date" section with days until race, current training phase, and taper timing guidance (e.g., "consider beginning taper 3-4 weeks before race").

**Checkpoint**: US3 complete — race date context shown

---

## Phase 6: User Story 4 - JSON Output (Priority: P4)

**Goal**: Structured JSON output for agent consumption

**Independent Test**: Run with `--json` flag and verify valid parseable JSON

### Implementation for User Story 4

- [x] T024 [US4] Add JSON output to predict CLI in `src/openactivity/cli/strava/predict.py` — when `--json` flag active, output JSON with all fields per contract spec: prediction (times, pace, confidence), reference_efforts array, readiness (overall, label, components), race_date context if provided. Handle insufficient data with error JSON.

**Checkpoint**: US4 complete — valid JSON with all prediction data

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validation, testing, and cleanup

- [x] T025 Run all tests with `pytest tests/unit/test_predict.py -v` and fix any failures
- [x] T026 Run `ruff check src/openactivity/analysis/predict.py src/openactivity/cli/strava/predict.py` and fix lint issues
- [x] T027 Manual validation: run `openactivity strava predict --distance 10K` on real synced data and verify prediction output
- [x] T028 Manual validation: run `openactivity --json strava predict --distance half` and verify JSON output
- [x] T029 Manual validation: run `openactivity strava predict --distance marathon --race-date 2026-06-15` and verify race-date context

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2
- **US2 (Phase 4)**: Depends on US1 (enhances predict orchestrator and CLI output)
- **US3 (Phase 5)**: Depends on US1 (adds flag to existing command)
- **US4 (Phase 6)**: Depends on US1+US2 (adds JSON for all data)
- **Polish (Phase 7)**: Depends on all user stories

### Parallel Opportunities

- T006, T007, T008 (US1 tests) can run in parallel
- T012, T013 (US2 tests) can run in parallel
- US3 and US4 can proceed in parallel after US2

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002-T005)
3. Complete Phase 3: User Story 1 (T006-T011)
4. **STOP and VALIDATE**: `openactivity strava predict --distance 10K` shows prediction
5. Continue to US2, US3, US4

### Incremental Delivery

1. Setup + Foundational → Riegel prediction engine ready
2. Add US1 → Race prediction visible (MVP!)
3. Add US2 → Readiness score with breakdown
4. Add US3 → Race-date context
5. Add US4 → JSON output for agents
6. Polish → Tests pass, lint clean, manual validation

---

## Notes

- No database schema changes — all computation on-the-fly from Activity + PersonalRecord data
- Riegel formula: T2 = T1 * (D2/D1)^1.06
- Standard distances: 1mi (1609.34m), 5K (5000m), 10K (10000m), Half (21097.5m), Marathon (42195m)
- Readiness weights: consistency 30%, volume trend 25%, taper status 25%, PR recency 20%
- Readiness labels: Not Ready (0-40), Building (41-60), Almost Ready (61-80), Race Ready (81-100)
- Confidence interval: ±2% base, widens with sparse/old data
- Reuses: records.py (best efforts), blocks.py (weekly aggregation), queries.py (data access)
