# Implementation Plan: Custom Time-Range Comparisons

**Branch**: `003-time-range-compare` | **Date**: 2026-03-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-time-range-compare/spec.md`

## Summary

Add a `compare` subcommand to the existing `openactivity strava analyze` command group that aggregates activity metrics across two user-specified date ranges and displays a side-by-side comparison table with deltas and percentage changes. This builds on the existing `analysis/summary.py` aggregation pattern and `db/queries.py` filtering. No new dependencies, models, or external integrations required — purely a new analysis module and CLI command wired into the existing architecture.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: typer (CLI), rich (terminal output), sqlalchemy (ORM) — all existing
**Storage**: SQLite at `~/.local/share/openactivity/openactivity.db` — no schema changes
**Testing**: pytest + pytest-cov — unit tests for comparison logic, CLI output tests
**Target Platform**: macOS, Linux, Windows (pip install / pipx)
**Project Type**: CLI
**Performance Goals**: <2s for comparison across 5,000 activities, <200ms for typical use (<500 activities)
**Constraints**: <256MB memory, no network calls, operates entirely on locally synced data
**Scale/Scope**: Single user, up to 10,000+ activities, 1 new CLI command, 1 new analysis module

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality | Pass | Type hints on all public functions. Actionable error messages for invalid date ranges. Structured error handling for edge cases. |
| II. Testing Standards | Pass | Unit tests for comparison aggregation logic (success + empty ranges). CLI output tests for table and JSON formats. No live API calls — uses local DB. |
| III. User Experience Consistency | Pass | Follows existing `analyze` subcommand pattern. `--json` supported. Errors to stderr, data to stdout. `--help` with usage examples. |
| IV. Simplicity | Pass | Single new module (`analysis/compare.py`) + single new CLI command. Reuses existing `get_activities` query helper. No new abstractions. |
| V. Maintainability | Pass | Isolated in analysis module. No changes to existing code beyond registering the new command. No circular deps. |
| VI. Performance | Pass | Single DB query per range using existing indexed filters. Aggregation in Python is O(n) on activity count. Well within 200ms for typical datasets. |
| API Provider Standards | Pass | No provider changes. Operates on already-synced local data. |

**Post-Phase 1 re-check**: All gates still pass. No violations requiring complexity justification.

## Project Structure

### Documentation (this feature)

```text
specs/003-time-range-compare/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli-commands.md  # CLI command contract
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/openactivity/
├── analysis/
│   └── compare.py       # NEW — comparison aggregation logic
├── cli/strava/
│   └── analyze.py       # MODIFIED — add compare subcommand
├── db/
│   └── queries.py       # EXISTING — reuse get_activities with after/before filters
└── output/
    └── units.py         # EXISTING — reuse format_distance, format_duration, etc.

tests/
└── unit/
    └── test_compare.py  # NEW — comparison logic tests
```

**Structure Decision**: Follows the established pattern from existing analysis modules (summary.py, pace.py, zones.py, power.py). New logic lives in `analysis/compare.py`, new CLI wiring in the existing `cli/strava/analyze.py`, and tests in `tests/unit/`.

## Complexity Tracking

No constitution violations. No complexity justification needed.
