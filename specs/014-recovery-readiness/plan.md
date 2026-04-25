# Implementation Plan: Recovery & Readiness Score

**Branch**: `014-recovery-readiness` | **Date**: 2026-04-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/014-recovery-readiness/spec.md`

## Summary

Add a daily readiness score (0-100) combining Garmin health metrics (HRV, sleep) with training load (TSB, volume trend) into a single actionable recommendation. New `openactivity analyze readiness` command with `--last` trend support and `--json` output. No schema changes — computed on-the-fly from existing `garmin_daily_summary` and activity data.

## Technical Context

**Language/Version**: Python 3.12+ (existing)
**Primary Dependencies**: typer (CLI), rich (terminal output), sqlalchemy (ORM) — all existing, no new deps
**Storage**: SQLite at `~/.local/share/openactivity/openactivity.db` — no schema changes
**Testing**: pytest (existing)
**Target Platform**: macOS/Linux CLI
**Project Type**: CLI tool
**Performance Goals**: Readiness computation < 2 seconds for 2 years of data
**Constraints**: Must gracefully degrade when Garmin health data is missing
**Scale/Scope**: Single user, local data

## Constitution Check

*GATE: All principles checked.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality | PASS | New module follows existing patterns, typed functions |
| II. Testing | PASS | Unit tests for scoring logic, integration test for CLI |
| III. UX Consistency | PASS | Added under `openactivity analyze readiness` + strava alias |
| IV. Simplicity | PASS | No new deps, no abstractions — 1 module, 1 command |
| V. Maintainability | PASS | Isolated in `analysis/readiness.py`, no circular deps |
| VI. Performance | PASS | On-the-fly computation from indexed tables |

## Project Structure

### Documentation (this feature)

```text
specs/014-recovery-readiness/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli-commands.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (new/modified files)

```text
src/openactivity/
├── analysis/
│   └── readiness.py          # NEW — core readiness computation
├── db/
│   └── queries.py            # MODIFIED — add Garmin health query functions
├── cli/
│   ├── analyze.py            # MODIFIED — add readiness command
│   └── strava/
│       └── analyze.py        # MODIFIED — add readiness alias

tests/
├── unit/
│   └── test_readiness.py     # NEW — unit tests for scoring logic
```

**Structure Decision**: Single new analysis module + query helpers. Follows existing pattern exactly (analysis module + CLI command + queries).
