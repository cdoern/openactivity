# Implementation Plan: Race Predictor & Readiness Score

**Branch**: `007-race-predictor` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-race-predictor/spec.md`

## Summary

Predict race times using the Riegel formula from personal record best efforts, with a composite readiness score (0-100) based on training consistency, volume trend, taper status, and PR recency. New CLI command `openactivity strava predict` with `--distance`, `--race-date`, and `--type` flags. All computation on-the-fly — no schema changes.

## Technical Context

**Language/Version**: Python 3.12+ — existing project
**Primary Dependencies**: typer (CLI), rich (terminal output), sqlalchemy (ORM) — all existing
**Storage**: SQLite at `~/.local/share/openactivity/openactivity.db` — no schema changes
**Testing**: pytest — existing
**Target Platform**: macOS/Linux CLI
**Project Type**: CLI application — existing
**Performance Goals**: Prediction completes in <5 seconds
**Constraints**: <200ms for local queries, <256MB memory
**Scale/Scope**: Single user, up to 10,000 activities

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality | PASS | New module follows single-responsibility; type annotations on public functions |
| II. Testing Standards | PASS | Unit tests for Riegel formula, readiness components, and edge cases |
| III. UX Consistency | PASS | Provider-first hierarchy (`strava predict`), `--json` support, `--help` text |
| IV. Simplicity | PASS | Reuses existing records.py, blocks.py, queries.py — no new abstractions |
| V. Maintainability | PASS | Isolated in analysis/predict.py + cli/strava/predict.py, no circular deps |
| VI. Performance | PASS | On-the-fly computation from local DB, well within constraints |

## Project Structure

### Documentation (this feature)

```text
specs/007-race-predictor/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli-commands.md
└── tasks.md
```

### Source Code (repository root)

```text
src/openactivity/
├── analysis/
│   └── predict.py          # NEW — Riegel formula, readiness score, orchestration
├── cli/strava/
│   ├── app.py              # MODIFIED — register predict subcommand
│   └── predict.py          # NEW — typer command with Rich output
└── (existing modules reused: db/queries.py, analysis/records.py, analysis/blocks.py)

tests/
└── unit/
    └── test_predict.py     # NEW — unit tests
```

**Structure Decision**: Single new analysis module + single new CLI module. Reuses existing records system for best efforts and blocks system for weekly aggregation. No new DB models.

## Key Reuse Points

- `analysis/records.py`: `find_best_effort_for_distance()` — sliding window for best effort at a distance
- `db/queries.py`: `get_personal_records()`, `get_activities()` — data access
- `analysis/blocks.py`: `aggregate_weeks()`, `compute_week_intensity()` — weekly metrics for readiness
- `output/units.py`: `format_distance()`, `format_duration()`, `format_speed_as_pace()` — formatting
