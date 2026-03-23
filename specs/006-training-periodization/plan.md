# Implementation Plan: Training Block / Periodization Detector

**Branch**: `006-training-periodization` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-training-periodization/spec.md`

## Summary

Add automatic training phase detection that classifies weeks into base, build, peak, or recovery phases based on weekly volume and intensity patterns. Groups consecutive similar weeks into named training blocks with timeline display. New `openactivity strava analyze blocks` command with time window and activity type filters. All computations on-the-fly from existing activity data — no schema changes needed.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: typer (CLI), rich (terminal output), sqlalchemy (ORM) — all existing
**Storage**: SQLite at `~/.local/share/openactivity/openactivity.db` — no schema changes
**Testing**: pytest + pytest-cov — unit tests for classification algorithm
**Target Platform**: macOS, Linux, Windows (pip install / pipx)
**Project Type**: CLI
**Performance Goals**: <3s for 26 weeks, <5s for 52 weeks
**Constraints**: <256MB memory, no network calls, operates on locally synced data
**Scale/Scope**: Single user, up to 10,000+ activities, 1 new analysis module, 1 new CLI command

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality | Pass | Type hints on all public functions. Actionable error messages for insufficient data. |
| II. Testing Standards | Pass | Unit tests for week classification, block grouping, intensity scoring. No live API calls. |
| III. User Experience Consistency | Pass | New `blocks` command under `analyze`. `--json` on all output. |
| IV. Simplicity | Pass | One new analysis module. On-the-fly computation avoids schema changes. Reuses existing query infrastructure. |
| V. Maintainability | Pass | Isolated in analysis/blocks.py. Modifications to analyze.py are additive only. |
| VI. Performance | Pass | O(n) aggregation over activities. No stream processing needed — uses activity-level metrics. |
| API Provider Standards | Pass | No provider changes. Operates on already-synced local activity data. |

**Post-Phase 1 re-check**: All gates still pass. No violations requiring complexity justification.

## Project Structure

### Documentation (this feature)

```text
specs/006-training-periodization/
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
│   └── blocks.py        # NEW — week aggregation, classification, block grouping
├── cli/strava/
│   └── analyze.py       # MODIFIED — add blocks command

tests/
└── unit/
    └── test_blocks.py   # NEW — classification and grouping tests
```

**Structure Decision**: Follows the established pattern. New analysis logic in `analysis/blocks.py`. New command added to existing `cli/strava/analyze.py`.

## Complexity Tracking

No constitution violations. No complexity justification needed.
