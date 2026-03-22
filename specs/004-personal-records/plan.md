# Implementation Plan: Personal Records Database

**Branch**: `004-personal-records` | **Date**: 2026-03-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-personal-records/spec.md`

## Summary

Add a personal records system that scans activity stream data to detect best efforts at standard running distances (1mi, 5K, 10K, half, marathon) and cycling power durations (5s, 1m, 5m, 20m, 60m). Records are persisted for instant lookup with full PR progression history. New `openactivity strava records` command group with scan, list, history, add-distance, and remove-distance subcommands. Extends the existing analysis and stream infrastructure.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: typer (CLI), rich (terminal output), sqlalchemy (ORM) — all existing
**Storage**: SQLite at `~/.local/share/openactivity/openactivity.db` — new tables for PersonalRecord and CustomDistance
**Testing**: pytest + pytest-cov — unit tests for scanning algorithm and record management
**Target Platform**: macOS, Linux, Windows (pip install / pipx)
**Project Type**: CLI
**Performance Goals**: <30s scan for 1,000 activities, <1s for list/history queries
**Constraints**: <256MB memory, no network calls, operates entirely on locally synced data
**Scale/Scope**: Single user, up to 10,000+ activities, 5 new CLI commands, 2 new DB models, 1 new analysis module

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality | Pass | Type hints on all public functions. Actionable error messages for invalid distances, missing streams. |
| II. Testing Standards | Pass | Unit tests for sliding window algorithm, record management, CLI output. No live API calls — uses local DB. |
| III. User Experience Consistency | Pass | New `records` command group under `strava`. `--json` on all commands. `--help` with examples. |
| IV. Simplicity | Pass | Two new models, one analysis module, one CLI module. Reuses existing stream query infrastructure. |
| V. Maintainability | Pass | Isolated in analysis/records.py and cli/strava/records.py. No changes to existing provider code. |
| VI. Performance | Pass | Sliding window is O(n) per activity per distance. Incremental scan avoids re-processing. Queries indexed. |
| API Provider Standards | Pass | No provider changes. Operates on already-synced local stream data. |

**Post-Phase 1 re-check**: All gates still pass. No violations requiring complexity justification.

## Project Structure

### Documentation (this feature)

```text
specs/004-personal-records/
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
│   └── records.py       # NEW — PR scanning, sliding window, record management
├── cli/strava/
│   ├── app.py           # MODIFIED — register records command group
│   └── records.py       # NEW — records CLI commands (scan, list, history, add/remove-distance)
├── db/
│   ├── models.py        # MODIFIED — add PersonalRecord and CustomDistance models
│   └── queries.py       # MODIFIED — add record query helpers

tests/
└── unit/
    └── test_records.py  # NEW — scanning algorithm and record management tests
```

**Structure Decision**: Follows the established pattern. New analysis logic in `analysis/records.py`, new CLI commands in `cli/strava/records.py`, new models added to existing `db/models.py`.

## Complexity Tracking

No constitution violations. No complexity justification needed.
