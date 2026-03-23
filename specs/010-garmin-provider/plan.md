# Implementation Plan: Garmin Connect Provider

**Branch**: `010-garmin-provider` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-garmin-provider/spec.md`

## Summary

Add Garmin Connect as a second data provider alongside Strava, enabling users to sync activities and unique health metrics (HRV, Body Battery, sleep data). Implement provider-agnostic commands that work across both providers while maintaining provider-specific features. Extend Activity model with provider field and implement deduplication logic to link matching activities from both sources.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: typer (CLI), rich (output), sqlalchemy (ORM), keyring (credentials), garminconnect (Garmin API)
**Storage**: SQLite at `~/.local/share/openactivity/openactivity.db` (existing database, schema migration required)
**Testing**: pytest with unit tests, integration tests using VCR.py for API mocking
**Target Platform**: Linux/macOS/Windows CLI
**Project Type**: CLI tool
**Performance Goals**: Auth < 1min, sync 100 activities < 5min, incremental sync < 30sec
**Constraints**: <500ms CLI startup for non-sync commands, <256MB memory during sync, offline-capable queries <200ms
**Scale/Scope**: Multi-provider support (2 initially: Strava + Garmin), 10k+ activities per user, ~15 new commands

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Code Quality ✅
- **Status**: PASS
- **Notes**: Following existing patterns from Strava provider. All new code will have linting (ruff), type annotations, structured error handling.

### Testing Standards ✅
- **Status**: PASS
- **Notes**: Will include unit tests for auth, sync, transformation logic. Integration tests with recorded Garmin API responses. Contract tests to validate provider interface conformance.

### User Experience Consistency ✅
- **Status**: PASS
- **Notes**: Follows constitution's provider-first hierarchy:
  - Provider-specific: `openactivity garmin auth|sync|athlete|daily` (Garmin-unique features)
  - Top-level unified: `openactivity activity <ID>`, `openactivity activities list --provider {strava|garmin}`
  - All commands support `--json` flag
  - Help text and progress indicators included

### Simplicity ✅
- **Status**: PASS
- **Notes**: Garmin provider implements shared interface (auth, sync, list activities) plus provider-specific extensions (health data). Follows YAGNI - minimal abstraction, pattern already established by Strava provider.

### Maintainability ✅
- **Status**: PASS
- **Notes**: Provider isolation principle maintained - Garmin module is self-contained at `src/openactivity/providers/garmin/`. No changes to Strava provider or core logic required. Clear ownership boundaries.

### Performance Requirements ✅
- **Status**: PASS
- **Notes**: Incremental sync reduces API load. Pagination supported. Local queries use indexed columns. Memory footprint minimal (streaming data writes).

### API Provider Integration Standards ✅
- **Status**: PASS
- **Notes**: Implements minimal shared interface (auth, sync, list). Garmin-specific data (HRV, Body Battery, sleep) stored in separate tables. Credentials in OS keyring. Rate limiting with backoff.

### Development Workflow ✅
- **Status**: PASS
- **Notes**: PR-based workflow, CI runs linting/tests, semantic versioning followed.

## Project Structure

### Documentation (this feature)

```text
specs/010-garmin-provider/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - garminconnect library research
├── data-model.md        # Phase 1 output - database schema design
├── quickstart.md        # Phase 1 output - getting started guide
├── contracts/           # Phase 1 output - CLI command schemas
│   └── cli-commands.md  # Command structure documentation
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created yet)
```

### Source Code (repository root)

```text
src/openactivity/
├── providers/
│   ├── interface.py              # Shared provider interface (existing)
│   ├── strava/                   # Existing Strava provider
│   └── garmin/                   # NEW: Garmin provider module
│       ├── __init__.py
│       ├── client.py             # Garmin Connect API client wrapper
│       ├── auth.py               # Username/password authentication
│       ├── sync.py               # Activity and health data sync logic
│       └── transform.py          # Garmin API → local model transformation
├── cli/
│   ├── root.py                   # MODIFIED: Register garmin command group
│   ├── activities.py             # MODIFIED: Provider-agnostic activity commands
│   ├── strava/                   # Existing Strava commands (unchanged)
│   └── garmin/                   # NEW: Garmin command group
│       ├── __init__.py
│       ├── app.py                # Garmin command group root
│       ├── auth.py               # `garmin auth` command
│       ├── sync.py               # `garmin sync` command
│       ├── athlete.py            # `garmin athlete` command
│       ├── activities.py         # `garmin activities` commands
│       └── daily.py              # `garmin daily` command (health data)
├── db/
│   ├── models.py                 # MODIFIED: Add provider fields to Activity
│   │                             # NEW: GarminDailySummary, GarminSleepSession models
│   ├── queries.py                # MODIFIED: Provider-aware queries
│   └── migrations/               # NEW: Alembic migration for schema changes
│       └── add_provider_fields.py
└── auth/
    └── keyring.py                # MODIFIED: Support Garmin credentials

tests/
├── unit/
│   ├── test_garmin_auth.py       # NEW: Garmin auth unit tests
│   ├── test_garmin_sync.py       # NEW: Garmin sync unit tests
│   └── test_garmin_transform.py  # NEW: Data transformation tests
├── integration/
│   └── test_garmin_provider.py   # NEW: Integration tests with VCR recordings
└── contract/
    └── test_provider_interface.py # MODIFIED: Include Garmin in contract tests
```

**Structure Decision**: Single project structure (existing). Garmin provider follows the same modular pattern as Strava: isolated provider module (`providers/garmin/`), dedicated CLI command group (`cli/garmin/`), provider-specific tests. Database layer extended with migration for multi-provider support. No architectural changes - pure extension following established patterns.

## Complexity Tracking

> No constitution violations - all complexity justified and within guidelines.

