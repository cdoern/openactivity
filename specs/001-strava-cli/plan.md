# Implementation Plan: OpenActivity Strava CLI

**Branch**: `001-strava-cli` | **Date**: 2026-03-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-strava-cli/spec.md`

## Summary

Build a Python CLI tool (`openactivity`) with Strava as the first provider. The CLI follows a provider-first command hierarchy (`openactivity strava <command>`). Users authenticate with their own Strava API credentials, sync activity data to local SQLite storage, then query, analyze, and export data offline. Key differentiator: derived analytics (pace trends, zone distributions, power curves) that Strava's web UI doesn't readily surface. Python chosen for its dominant fitness API library ecosystem (stravalib, python-garminconnect for future providers).

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: typer (CLI), rich (terminal output), sqlalchemy (ORM), stravalib (Strava API), keyring (credentials), matplotlib (charts), gpxpy (GPX export), httpx (HTTP client)
**Storage**: SQLite (embedded, WAL mode) at `~/.local/share/openactivity/openactivity.db`
**Testing**: pytest + pytest-cov + VCR.py (recorded API responses)
**Target Platform**: macOS, Linux, Windows (pip install / pipx)
**Project Type**: CLI
**Performance Goals**: <500ms startup, <200ms local queries (10k activities), <10s analysis (1k activities)
**Constraints**: <256MB memory, no network calls except during `sync` and `auth`, user-managed API keys
**Scale/Scope**: Single user, up to 10,000+ activities, ~15 CLI commands

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality | ✅ Pass | Type hints throughout. Structured error handling. Linting via ruff. Formatting via ruff format. |
| II. Testing Standards | ✅ Pass | pytest with parameterized tests. Integration tests with VCR.py recorded responses (no live calls). Contract tests for provider interface. |
| III. UX Consistency | ✅ Pass | Provider-first hierarchy (`openactivity strava <cmd>`). `--json` on all commands. stderr for errors, stdout for data. `--help` with examples on every command. Progress indicators via Rich. |
| IV. Simplicity | ✅ Pass | Minimal shared provider interface (auth, sync, list). Single config format (TOML). stravalib handles Strava API complexity. Dependencies justified in research.md. |
| V. Maintainability | ✅ Pass | Strava provider isolated in `src/openactivity/providers/strava/`. No circular deps. Conventional commits. |
| VI. Performance | ✅ Pass | Python startup ~200-400ms (within 500ms limit). SQLite with indexes for <200ms queries. Incremental sync. Memory well under 256MB. |
| API Provider Standards | ✅ Pass | Strava as isolated module. Credentials in OS keychain. Rate limiting with auto-backoff. Shared activity model + provider-specific storage. |

**Post-Phase 1 re-check**: All gates still pass. No violations requiring complexity justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-strava-cli/
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
src/
└── openactivity/
    ├── __init__.py
    ├── main.py                      # Typer app entry point
    ├── cli/
    │   ├── __init__.py
    │   ├── root.py                  # Root app, global options
    │   └── strava/
    │       ├── __init__.py
    │       ├── app.py               # `openactivity strava` command group
    │       ├── auth.py              # auth, auth revoke
    │       ├── sync.py              # sync command
    │       ├── athlete.py           # athlete command
    │       ├── activities.py        # activities list, activity <ID>
    │       ├── analyze.py           # analyze summary, pace, zones, power-curve
    │       ├── segments.py          # segments list, segment <ID> efforts/leaderboard
    │       └── export.py            # export commands
    ├── providers/
    │   ├── __init__.py
    │   ├── interface.py             # Shared provider interface (Protocol)
    │   └── strava/
    │       ├── __init__.py
    │       ├── client.py            # Strava API client (wraps stravalib)
    │       ├── oauth.py             # OAuth2 flow implementation
    │       ├── sync.py              # Sync logic (incremental, rate limiting)
    │       └── transform.py         # stravalib models → local model conversion
    ├── db/
    │   ├── __init__.py
    │   ├── database.py              # Engine, session, initialization
    │   ├── models.py                # SQLAlchemy model definitions
    │   └── queries.py               # Common query helpers
    ├── analysis/
    │   ├── __init__.py
    │   ├── summary.py               # Training volume aggregation
    │   ├── pace.py                  # Pace trend computation
    │   ├── zones.py                 # Zone distribution aggregation
    │   └── power.py                 # Power curve computation
    ├── export/
    │   ├── __init__.py
    │   ├── gpx.py                   # GPX file generation
    │   ├── csv.py                   # CSV export
    │   └── chart.py                 # Chart generation (matplotlib)
    ├── config/
    │   ├── __init__.py
    │   └── config.py                # TOML config management
    ├── auth/
    │   ├── __init__.py
    │   └── keyring.py               # OS keychain credential storage
    └── output/
        ├── __init__.py
        ├── table.py                 # Rich table formatting
        ├── json.py                  # JSON output
        ├── errors.py                # Structured error output
        └── units.py                 # Unit conversion (metric/imperial)

tests/
├── conftest.py                      # Shared fixtures
├── unit/
│   ├── test_analysis.py
│   ├── test_units.py
│   └── test_transform.py
├── integration/
│   ├── test_auth.py
│   ├── test_sync.py
│   └── cassettes/                   # VCR.py recorded API responses
└── contract/
    └── test_provider_interface.py

pyproject.toml                       # Project config, dependencies, entry points
```

**Structure Decision**: Standard Python package layout with `src/` directory. Provider isolation achieved via `src/openactivity/providers/strava/` package — adding a future provider (e.g., Garmin) means adding `src/openactivity/providers/garmin/` and `src/openactivity/cli/garmin/` with no changes to existing code.

## Complexity Tracking

> No constitution violations. No complexity justification needed.
