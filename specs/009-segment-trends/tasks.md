# Tasks: Segment Trend Analysis

**Input**: Design documents from `/specs/009-segment-trends/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: No new project setup needed — all dependencies exist. This phase adds the foundational query support.

- [ ] T001 Add ascending-order segment efforts query function in src/openactivity/db/queries.py

---

## Phase 2: Foundational (Core Analysis Module)

**Purpose**: Core trend computation logic that US1-US4 all depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T002 Create segment trend analysis module with linear regression, trend classification, and effort summary computation in src/openactivity/analysis/segments.py
- [ ] T003 Create unit tests for segment trend analysis in tests/unit/test_segment_trends.py

**Checkpoint**: Trend analysis engine ready — CLI work can now begin.

---

## Phase 3: User Story 1 - View Segment Performance Trend (Priority: P1) MVP

**Goal**: User runs `segment <ID> trend` and sees trend direction, rate of change, best/worst/recent effort, and effort history.

**Independent Test**: Run `openactivity strava segment <ID> trend` with a segment that has 3+ efforts and verify trend direction, rate of change, and effort summary are displayed.

### Implementation for User Story 1

- [ ] T004 [US1] Add `trend` subcommand to segment CLI with human-readable output in src/openactivity/cli/strava/segments.py
- [ ] T005 [US1] Register segment trend subcommand in src/openactivity/cli/strava/app.py
- [ ] T006 [US1] Handle edge cases (segment not found, no efforts, <3 efforts) with informative error messages in src/openactivity/cli/strava/segments.py

**Checkpoint**: User Story 1 fully functional — `segment <ID> trend` shows trend analysis.

---

## Phase 4: User Story 2 - Segment List with Trend Indicators (Priority: P2)

**Goal**: `segments list` shows trend column (↑/↓/→/—) and rate of change for each segment.

**Independent Test**: Run `openactivity strava segments list` and verify trend indicator column appears.

### Implementation for User Story 2

- [ ] T007 [US2] Add trend indicator and rate columns to segments list output in src/openactivity/cli/strava/segments.py
- [ ] T008 [US2] Add trend indicator tests in tests/unit/test_segment_trends.py

**Checkpoint**: Segments list now shows at-a-glance trend info.

---

## Phase 5: User Story 3 - HR-Adjusted Trend (Priority: P3)

**Goal**: When HR data is available, show an HR-adjusted trend alongside the raw trend.

**Independent Test**: Run `segment <ID> trend` on a segment with HR data and verify HR-adjusted section appears.

### Implementation for User Story 3

- [ ] T009 [US3] Add HR-adjusted trend computation to analysis module in src/openactivity/analysis/segments.py
- [ ] T010 [US3] Add HR-adjusted trend display to trend CLI output in src/openactivity/cli/strava/segments.py
- [ ] T011 [US3] Add HR-adjusted trend tests in tests/unit/test_segment_trends.py

**Checkpoint**: HR-adjusted trend shown when HR data available.

---

## Phase 6: User Story 4 - JSON Output (Priority: P4)

**Goal**: `--json` flag produces valid JSON with all trend data.

**Independent Test**: Run with `--json` flag and verify valid JSON output.

### Implementation for User Story 4

- [ ] T012 [US4] Add JSON output rendering for segment trend command in src/openactivity/cli/strava/segments.py
- [ ] T013 [US4] Add JSON output for trend indicators in segments list in src/openactivity/cli/strava/segments.py

**Checkpoint**: JSON output works for both trend command and segments list.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T014 Run full test suite and fix any failures
- [ ] T015 Run linting/formatting checks and fix issues

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (query function)
- **US1 (Phase 3)**: Depends on Phase 2 (analysis module)
- **US2 (Phase 4)**: Depends on Phase 2 (analysis module), independent of US1
- **US3 (Phase 5)**: Depends on US1 (extends trend output)
- **US4 (Phase 6)**: Depends on US1 and US2 (adds JSON to existing commands)
- **Polish (Phase 7)**: Depends on all stories complete

### User Story Dependencies

- **US1 (P1)**: Core — no dependencies on other stories
- **US2 (P2)**: Independent of US1 — only depends on analysis module
- **US3 (P3)**: Extends US1 trend output — depends on US1
- **US4 (P4)**: Adds JSON to US1 and US2 outputs — depends on both

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Query support
2. Complete Phase 2: Analysis module + tests
3. Complete Phase 3: User Story 1 (trend command)
4. **STOP and VALIDATE**: Test `segment <ID> trend` independently

### Incremental Delivery

1. Setup + Foundational → Analysis engine ready
2. Add US1 → Trend command works (MVP!)
3. Add US2 → Segments list enhanced
4. Add US3 → HR-adjusted trends
5. Add US4 → JSON output for all commands

---

## Notes

- No new database tables or schema changes
- scipy.stats.linregress already available (added in 008-correlation-engine)
- All computation is on-the-fly from existing SegmentEffort data
- Stable threshold: ±1 second/month per spec assumption
