# Tasks: Recovery & Readiness Score

**Input**: Design documents from `/specs/014-recovery-readiness/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new project setup needed — existing project structure.

*(No tasks — project already initialized)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add Garmin health data query functions and core readiness computation module.

- [x] T001 Add `get_daily_summaries(session, after, before)` and `get_daily_summary(session, date)` query functions for GarminDailySummary in src/openactivity/db/queries.py
- [x] T002 Create readiness computation module at src/openactivity/analysis/readiness.py with: `compute_hrv_score()`, `compute_sleep_score()`, `compute_form_score()`, `compute_volume_score()`, `compute_readiness()` orchestrator, and `classify_readiness()` label/recommendation mapper

**Checkpoint**: Core readiness logic exists and can be unit tested standalone

---

## Phase 3: User Story 1 — Today's Readiness Score (Priority: P1)

**Goal**: User runs `openactivity analyze readiness` and gets today's score, label, component breakdown, and recommendation.

**Independent Test**: Run `openactivity analyze readiness` with Garmin health data and training history — see score and recommendation.

- [x] T003 [US1] Implement `compute_hrv_score(session, target_date)` in src/openactivity/analysis/readiness.py — query 8 days of GarminDailySummary, compute 7-day HRV baseline, score today's HRV vs baseline; optionally adjust with Body Battery and stress
- [x] T004 [P] [US1] Implement `compute_sleep_score(session, target_date)` in src/openactivity/analysis/readiness.py — query GarminDailySummary for target date, map sleep_score (0-100) to component score
- [x] T005 [P] [US1] Implement `compute_form_score(session, target_date)` in src/openactivity/analysis/readiness.py — call `compute_daily_tss()` and `compute_fitness_fatigue()` from fitness module, extract TSB for target date, map to 0-100 using piecewise thresholds from research.md
- [x] T006 [P] [US1] Implement `compute_volume_score(session, target_date)` in src/openactivity/analysis/readiness.py — get activities from last 14 days via `get_activities()`, sum distance for last-7d and prior-7d, score based on ratio (stable=high, spike=low)
- [x] T007 [US1] Implement `compute_readiness(session, target_date)` orchestrator in src/openactivity/analysis/readiness.py — call all 4 component functions, handle missing data with proportional weight redistribution, compute composite score, classify label and recommendation
- [x] T008 [US1] Add `readiness` command to src/openactivity/cli/analyze.py — `@app.command("readiness")` with `--last` and `--provider` options, Rich output showing score bar, component breakdown, and recommendation (today-only mode)
- [x] T009 [US1] Add `readiness` alias to src/openactivity/cli/strava/analyze.py — thin wrapper calling top-level readiness with `provider="strava"`

**Checkpoint**: `openactivity analyze readiness` shows today's score with full or partial components

---

## Phase 4: User Story 2 — Readiness Trend Over Time (Priority: P2)

**Goal**: User runs `openactivity analyze readiness --last 30d` and sees daily readiness scores in a table.

**Independent Test**: Run with `--last 30d` — see table of daily scores with averages.

- [x] T010 [US2] Implement `compute_readiness_trend(session, days)` in src/openactivity/analysis/readiness.py — loop over each day in window, call `compute_readiness()` per day, collect results into a list with summary stats (average, best, worst)
- [x] T011 [US2] Update `readiness` command in src/openactivity/cli/analyze.py — when `--last` is provided, call `compute_readiness_trend()` and render Rich table with Date, Score, Label, HRV, Sleep, Form, Volume columns plus summary line

**Checkpoint**: `openactivity analyze readiness --last 30d` shows daily trend table

---

## Phase 5: User Story 3 — JSON Output (Priority: P3)

**Goal**: `openactivity --json analyze readiness` outputs machine-parseable JSON matching the contract.

**Independent Test**: Run with `--json` flag — validate output matches contract schema.

- [x] T012 [US3] Add JSON output path to `readiness` command in src/openactivity/cli/analyze.py — for today-only: output `{date, score, label, recommendation, components}`, for `--last`: output `{today, daily, summary}` per contracts/cli-commands.md

**Checkpoint**: JSON output matches contract for both today-only and trend modes

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T013 [P] Add unit tests for readiness scoring logic in tests/unit/test_readiness.py — test each component scorer, weight redistribution, label classification, and edge cases (missing data, partial data)
- [x] T014 Run full test suite and verify no regressions
- [x] T015 Update help text examples in readiness command to match quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 2 (Foundational)**: No dependencies — start immediately
- **Phase 3 (US1)**: Depends on T001, T002 completion
- **Phase 4 (US2)**: Depends on Phase 3 (US1) — reuses `compute_readiness()`
- **Phase 5 (US3)**: Depends on Phase 3 (US1) — adds JSON serialization
- **Phase 6 (Polish)**: After all user stories complete

### Parallel Opportunities

Within Phase 3: T003 must complete first (establishes module patterns), then T004, T005, T006 can run in parallel (independent component scorers in different functions). T007 depends on T003-T006. T008-T009 depend on T007.

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. T001-T002: Foundational queries and module skeleton
2. T003-T007: Core readiness computation
3. T008-T009: CLI command
4. **VALIDATE**: `openactivity analyze readiness` works

### Full Feature

5. T010-T011: Trend support
6. T012: JSON output
7. T013-T015: Tests and polish
