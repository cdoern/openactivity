# Implementation Plan: Grade-Adjusted Pace & Effort Scoring

**Branch**: `005-gap-effort` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-gap-effort/spec.md`

## Summary

Add Grade-Adjusted Pace (GAP) computation using the Minetti energy cost model and a normalized effort score (0-100) per activity. Extends the existing `openactivity strava activity <ID>` detail view with overall and per-lap GAP. New `openactivity strava analyze effort` command trends GAP and effort scores over time with configurable time window and activity type filters. All computations are on-the-fly from existing stream data — no schema changes needed.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: typer (CLI), rich (terminal output), sqlalchemy (ORM) — all existing
**Storage**: SQLite at `~/.local/share/openactivity/openactivity.db` — no schema changes
**Testing**: pytest + pytest-cov — unit tests for GAP algorithm and effort scoring
**Target Platform**: macOS, Linux, Windows (pip install / pipx)
**Project Type**: CLI
**Performance Goals**: <1s GAP computation per activity, <5s effort trend for 500 activities
**Constraints**: <256MB memory, no network calls, operates entirely on locally synced data
**Scale/Scope**: Single user, up to 10,000+ activities, 1 new analysis module, 1 new CLI command, modifications to existing activity detail view

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality | Pass | Type hints on all public functions. Actionable error messages for missing stream data. |
| II. Testing Standards | Pass | Unit tests for Minetti model, GAP computation, effort scoring. No live API calls. |
| III. User Experience Consistency | Pass | GAP added to existing `activity` detail view. New `effort` command under `analyze`. `--json` on all. |
| IV. Simplicity | Pass | One new analysis module. On-the-fly computation avoids schema changes. Reuses existing stream query infrastructure. |
| V. Maintainability | Pass | Isolated in analysis/gap.py. Modifications to activities.py are additive only. |
| VI. Performance | Pass | O(n) per stream for grade computation. On-the-fly avoids storage overhead. |
| API Provider Standards | Pass | No provider changes. Operates on already-synced local stream data. |

**Post-Phase 1 re-check**: All gates still pass. No violations requiring complexity justification.

## Project Structure

### Documentation (this feature)

```text
specs/005-gap-effort/
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
│   └── gap.py           # NEW — Minetti GAP computation, effort scoring, trend analysis
├── cli/strava/
│   ├── activities.py    # MODIFIED — add GAP to activity detail view
│   └── analyze.py       # MODIFIED — add effort trend command

tests/
└── unit/
    └── test_gap.py      # NEW — GAP algorithm and effort scoring tests
```

**Structure Decision**: Follows the established pattern. New analysis logic in `analysis/gap.py`. Activity detail view modified in `cli/strava/activities.py`. New effort command added to existing `cli/strava/analyze.py`.

## Complexity Tracking

No constitution violations. No complexity justification needed.
