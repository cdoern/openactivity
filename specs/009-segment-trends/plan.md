# Implementation Plan: Segment Trend Analysis

**Branch**: `009-segment-trends` | **Date**: 2026-03-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-segment-trends/spec.md`

## Summary

Add segment performance trend analysis using linear regression on elapsed time vs date. New `segment <ID> trend` command shows trend direction (improving/declining/stable), rate of change (seconds/month), effort history, and optional HR-adjusted trend. Extend `segments list` with trend indicator column. All computation is on-the-fly from existing SegmentEffort data — no schema changes.

## Technical Context

**Language/Version**: Python 3.12+ (existing)
**Primary Dependencies**: typer (CLI), rich (terminal output), sqlalchemy (ORM), scipy (linear regression) — all existing
**Storage**: SQLite at `~/.local/share/openactivity/openactivity.db` — no schema changes, reads from existing `segments` and `segment_efforts` tables
**Testing**: pytest with mock data — no live API calls
**Target Platform**: macOS/Linux CLI
**Project Type**: CLI tool
**Performance Goals**: Trend analysis in under 3 seconds (SC-001)
**Constraints**: <200ms for local queries, <256MB memory
**Scale/Scope**: Typical user has 10-50 starred segments with 3-50 efforts each

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality | PASS | Single-responsibility functions, type annotations, actionable errors |
| II. Testing Standards | PASS | Unit tests for analysis module, mock data fixtures |
| III. UX Consistency | PASS | Provider-first hierarchy (`strava segment <ID> trend`), `--json` support, `--help` |
| IV. Simplicity | PASS | No new dependencies (scipy already added in 008), no new abstractions |
| V. Maintainability | PASS | Analysis module isolated, no circular deps |
| VI. Performance | PASS | On-the-fly computation from local DB, well within constraints |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/009-segment-trends/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli-commands.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/openactivity/
├── analysis/
│   └── segments.py          # NEW: Segment trend computation (linear regression, HR-adjusted)
├── cli/strava/
│   ├── segments.py          # MODIFY: Add trend column to segments list
│   └── app.py               # MODIFY: Register segment trend subcommand
└── db/
    └── queries.py           # MODIFY: Add query for efforts ordered by date (ascending)

tests/
└── unit/
    └── test_segment_trends.py  # NEW: Tests for trend analysis
```

**Structure Decision**: Follows existing pattern — analysis logic in `analysis/segments.py`, CLI rendering in `cli/strava/segments.py`, queries in `db/queries.py`.
