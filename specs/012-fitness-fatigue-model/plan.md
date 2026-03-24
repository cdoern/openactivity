# Implementation Plan: Fitness/Fatigue Model (ATL/CTL/TSB)

**Branch**: `012-fitness-fatigue-model` | **Date**: 2026-03-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-fitness-fatigue-model/spec.md`

## Summary

Implement the classic Banister impulse-response fitness/fatigue model as `openactivity strava analyze fitness`. Compute TRIMP-based Training Stress Score (TSS) per activity from HR data, derive daily ATL (7-day decay, fatigue), CTL (42-day decay, fitness), and TSB (form = CTL - ATL). Classify training status. Add chart generation and per-activity TSS to activity detail. Uses data from both providers with cross-provider deduplication.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: typer (CLI), rich (terminal output), sqlalchemy (ORM), matplotlib (charts) — all existing
**Storage**: SQLite at `~/.local/share/openactivity/openactivity.db` — no schema changes, all computed on-the-fly
**Testing**: pytest
**Target Platform**: macOS, Linux
**Project Type**: CLI
**Performance Goals**: <2 seconds for 1 year of data (~200 activities)
**Constraints**: <200ms for local queries, <256MB memory
**Scale/Scope**: ~200 activities with HR, 1 new analysis module, 1 new CLI command, 1 file modified for TSS in detail view

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality | PASS | Single-responsibility functions, type annotations, actionable errors |
| II. Testing Standards | PASS | Unit tests for TSS/ATL/CTL math, integration test for CLI |
| III. UX Consistency | PASS | Follows exact same pattern as 9 existing analyze commands. --json supported. |
| IV. Simplicity | PASS | No new abstractions — one analysis module + one CLI command |
| V. Maintainability | PASS | Isolated analysis module, no circular deps |
| VI. Performance | PASS | Pure math on ~200 activities, well under 2 seconds |
| API Integration | PASS | No external API calls — local data only |
| Development Workflow | PASS | PR with tests, conventional commits |

**Post-Phase 1 re-check**: All gates pass. No new dependencies, no schema changes.

## Project Structure

### Documentation (this feature)

```text
specs/012-fitness-fatigue-model/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli-commands.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/openactivity/
├── analysis/
│   └── fitness.py              # NEW: TSS, ATL, CTL, TSB computation
├── cli/
│   └── strava/
│       ├── analyze.py          # MODIFY: add `fitness` command
│       └── activities.py       # MODIFY: add TSS to activity detail view

tests/
└── unit/
    └── test_fitness.py         # NEW: unit tests for TSS/ATL/CTL math
```

**Structure Decision**: Single project, existing layout. 1 new analysis module, 2 existing files modified, 1 test file.
