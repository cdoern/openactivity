# Implementation Plan: Cross-Provider Activity Linking

**Branch**: `011-cross-provider-linking` | **Date**: 2026-03-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-cross-provider-linking/spec.md`

## Summary

Wire up the existing `detect_duplicate_activities()` and `link_activities()` functions — which implement full matching logic but are never called — into a new `openactivity activities link` command for bulk linking, and auto-link hooks in both the Garmin importer and Strava sync provider. Fix the `_types_match()` function to handle actual type formats in the database (Strava's `root='Run'` wrapper vs Garmin's plain `Run`).

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: typer (CLI), rich (terminal output), sqlalchemy (ORM) — all existing, no new deps
**Storage**: SQLite at `~/.local/share/openactivity/openactivity.db` — no schema changes, `activity_links` table already exists
**Testing**: pytest
**Target Platform**: macOS, Linux
**Project Type**: CLI
**Performance Goals**: Bulk link 375+ activities in <5 seconds, auto-link adds <1s overhead
**Constraints**: <200ms for local queries, <256MB memory
**Scale/Scope**: ~375 activities (175 Garmin + 200 Strava), 4 files modified, 1 new command

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality | PASS | Single-responsibility functions, type annotations, actionable errors |
| II. Testing Standards | PASS | Unit tests for linking logic, integration test for auto-linking |
| III. UX Consistency | PASS | `activities link` fits provider-first hierarchy as cross-provider root command. --json supported. |
| IV. Simplicity | PASS | No new abstractions — wiring existing functions into existing call sites |
| V. Maintainability | PASS | No circular deps, provider adapters unchanged, linking logic stays in queries.py |
| VI. Performance | PASS | Time-based filtering limits candidates. <200ms for typical datasets. |
| API Integration | PASS | No new provider interfaces. Linking is a local-only DB operation. |
| Development Workflow | PASS | PR with tests, conventional commits |

**Post-Phase 1 re-check**: All gates still pass. No new dependencies, no schema changes, no abstraction layers.

## Project Structure

### Documentation (this feature)

```text
specs/011-cross-provider-linking/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research
├── data-model.md        # Phase 1 data model
├── quickstart.md        # Phase 1 quickstart guide
├── contracts/           # Phase 1 CLI contracts
│   └── cli-commands.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (next step)
```

### Source Code (repository root)

```text
src/openactivity/
├── db/
│   └── queries.py              # MODIFY: fix _types_match(), add bulk_link_activities()
├── cli/
│   └── strava/
│       └── activities.py       # MODIFY: add `link` command to activities app
├── providers/
│   ├── garmin/
│   │   └── importer.py         # MODIFY: add auto-link after import_from_directory()
│   └── strava/
│       └── sync.py             # MODIFY: add auto-link after sync_activities()

tests/
├── unit/
│   └── test_activity_linking.py    # NEW: unit tests for linking
└── integration/
    └── test_auto_linking.py        # NEW: integration tests for auto-link hooks
```

**Structure Decision**: Single project, existing layout. Only 4 source files modified, 2 test files added.
