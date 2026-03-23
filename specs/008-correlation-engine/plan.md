# Implementation Plan: Cross-Activity Correlation Engine

**Branch**: `008-correlation-engine` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-correlation-engine/spec.md`

## Summary

Compute Pearson and Spearman correlations between any two weekly training metrics with optional lag analysis. New `correlate` subcommand under `strava analyze`. Supports 9 metrics, lag offsets (0/1/2/4 weeks), strength labels, and statistical significance reporting. All computation on-the-fly — no schema changes.

## Technical Context

**Language/Version**: Python 3.12+ — existing project
**Primary Dependencies**: typer (CLI), rich (terminal output), sqlalchemy (ORM), scipy.stats (correlation) — scipy is new
**Storage**: SQLite at `~/.local/share/openactivity/openactivity.db` — no schema changes
**Testing**: pytest — existing
**Target Platform**: macOS/Linux CLI
**Project Type**: CLI application — existing
**Performance Goals**: Correlation completes in <5 seconds
**Constraints**: <200ms for local queries, <256MB memory
**Scale/Scope**: Single user, up to 10,000 activities, ~52 weeks per year

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality | PASS | New module, single responsibility, type annotations |
| II. Testing Standards | PASS | Unit tests for correlation math and metric aggregation |
| III. UX Consistency | PASS | Subcommand under `strava analyze`, `--json` support, `--help` |
| IV. Simplicity | PASS | scipy.stats justified — Pearson/Spearman with p-values not trivially reimplemented. Reuses aggregate_weeks from blocks.py |
| V. Maintainability | PASS | Isolated in analysis/correlate.py, no circular deps |
| VI. Performance | PASS | On-the-fly from local DB |

## Project Structure

### Documentation (this feature)

```text
specs/008-correlation-engine/
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
│   └── correlate.py        # NEW — metric aggregation, correlation computation
├── cli/strava/
│   └── analyze.py          # MODIFIED — add correlate subcommand
└── (existing modules reused: analysis/blocks.py, db/queries.py)

tests/
└── unit/
    └── test_correlate.py   # NEW — unit tests
```

**Structure Decision**: Single new analysis module. Correlate command added as subcommand of existing `analyze` app (same pattern as `effort`, `blocks`). Reuses `aggregate_weeks` from blocks.py for weekly grouping.

## Key Reuse Points

- `analysis/blocks.py`: `aggregate_weeks()` — groups activities into ISO weeks
- `db/queries.py`: `get_activities()` — data access with type/date filtering
- `output/units.py`: formatting utilities
- `output/json.py`: `print_json()` for JSON output

## New Dependency

- `scipy` — specifically `scipy.stats.pearsonr` and `scipy.stats.spearmanr`. Justified: computing correlation coefficients with p-values requires proper statistical functions. Reimplementing Pearson is trivial but Spearman rank correlation with p-values is not.
