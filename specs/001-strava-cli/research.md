# Research: OpenActivity Strava CLI

**Date**: 2026-03-13
**Feature**: 001-strava-cli

## Decision 1: Programming Language

**Decision**: Python 3.12+

**Rationale**: Python has the richest ecosystem for fitness platform API integrations. `stravalib` (973 stars, actively maintained) provides a complete Strava API client. `python-garminconnect` (1,574 stars) is the dominant Garmin library with 100+ API methods — no equivalent exists in Go or any other language. Since openactivity's core purpose is multi-provider fitness data integration, choosing the language with the best library support is critical. Python startup time (~200-400ms) is within the 500ms constitution limit.

**Alternatives considered**:
- **Go**: Faster startup (~10ms), single binary. Strava has an official Go library but it shows less activity. No Garmin library exists. Would require writing API clients from scratch for most providers.
- **Rust**: Minimal fitness API ecosystem. No mature Strava or Garmin libraries.
- **TypeScript/Node**: Strava support exists (375 stars) but no Garmin library. Weaker CLI tooling.

## Decision 2: CLI Framework

**Decision**: Typer (built on Click)

**Rationale**: Typer provides a modern, type-hint-driven CLI framework with automatic help generation, shell completions, and rich terminal output via Rich integration. Supports hierarchical command groups natively. Less boilerplate than Click while retaining its power. Well-suited for the provider-first command tree (`openactivity strava activities list`).

**Alternatives considered**:
- **Click**: More mature but more verbose. Typer wraps Click and adds type-hint-based argument parsing.
- **argparse**: Standard library but lacks subcommand hierarchy ergonomics and help formatting.

## Decision 3: Local Storage

**Decision**: SQLite via SQLAlchemy 2.0

**Rationale**: SQLite is embedded (zero user setup), handles 10,000+ activities easily. SQLAlchemy 2.0 provides an ORM with migrations (via Alembic), type-safe queries, and the ability to drop to raw SQL when needed. WAL mode for concurrent reads. Meets <200ms local query requirement with proper indexing.

**Alternatives considered**:
- **Raw sqlite3**: More control but slower development, no migrations.
- **Peewee**: Simpler ORM but less feature-rich for complex queries.
- **JSON files**: Would not scale for filtering/analysis across thousands of activities.

## Decision 4: Credential Storage

**Decision**: keyring (Python keyring library)

**Rationale**: Cross-platform abstraction over OS credential stores (macOS Keychain, Linux Secret Service, Windows Credential Manager). Well-maintained, widely used (e.g., by pip, twine). Client ID, client secret, and OAuth tokens stored in OS keychain.

**Alternatives considered**:
- **Encrypted config file**: Less secure than OS keychain, requires managing encryption keys.
- **Environment variables**: Not persistent, poor UX for CLI tool.

## Decision 5: Strava API Client

**Decision**: stravalib

**Rationale**: Most popular Strava API library (973 stars). Actively maintained with Python 3.13 support as of Jan 2026. Complete coverage of Strava API v3 including activities, streams, segments, athlete data, and OAuth2 flow. Handles pagination, rate limiting, and data model serialization.

**Alternatives considered**:
- **Custom HTTP client**: Unnecessary when a well-maintained, feature-complete library exists.

## Decision 6: HTTP Client (for non-stravalib needs)

**Decision**: httpx

**Rationale**: Modern async-capable HTTP client. Needed for any API calls not covered by stravalib (e.g., future providers). Drop-in replacement for requests with async support.

**Alternatives considered**:
- **requests**: Synchronous only, no async support.
- **aiohttp**: More complex API, less ergonomic.

## Decision 7: Table Rendering

**Decision**: Rich (rich.table)

**Rationale**: Rich provides beautiful terminal tables, progress bars, syntax highlighting, and markdown rendering. Single dependency covers table output, progress indicators for sync, and formatted error messages. Integrates naturally with Typer.

**Alternatives considered**:
- **tabulate**: Simpler but no progress bars or rich formatting.
- **prettytable**: Less actively maintained.

## Decision 8: Chart Generation

**Decision**: matplotlib

**Rationale**: Industry-standard Python charting library. Produces publication-quality PNG/SVG charts. Extensive customization for bar, line, scatter, and pie charts. Massive community and documentation. Suitable for training volume summaries, pace trends, zone distributions, and power curves.

**Alternatives considered**:
- **plotly**: Interactive HTML charts but heavier dependency. Better for web, not CLI file export.
- **seaborn**: Built on matplotlib but adds unnecessary abstraction for this use case.

## Decision 9: GPX Generation

**Decision**: gpxpy

**Rationale**: Well-maintained Python library for reading and writing GPX files. Supports GPX 1.1, track points with extensions (heart rate, cadence, power). Simple API for constructing GPX files from activity stream data.

**Alternatives considered**:
- **Manual XML generation**: Unnecessary when purpose-built library exists.

## Decision 10: Testing

**Decision**: pytest

**Rationale**: De facto standard for Python testing. Supports fixtures, parameterized tests (analogous to table-driven tests), and plugins for coverage (pytest-cov). Recorded API responses via pytest-recording or VCR.py for integration tests without live API calls.

**Alternatives considered**:
- **unittest**: Standard library but more verbose, less ergonomic.

## Decision 11: Configuration Format

**Decision**: TOML via tomllib (stdlib) + tomli-w

**Rationale**: TOML is human-readable and is Python's standard config format (pyproject.toml). tomllib is built into Python 3.11+. Single config file at `~/.config/openactivity/config.toml`. tomli-w for writing config changes.

**Alternatives considered**:
- **YAML**: Requires external dependency, indentation-sensitive.
- **JSON**: Poor for human editing (no comments).

## Decision 12: Package Management & Distribution

**Decision**: uv for development, pip-installable package

**Rationale**: uv provides fast dependency resolution and virtual environment management for development. Published as a pip-installable package (`pip install openactivity`) with a console_scripts entry point. Can also be installed via pipx for isolated CLI installs.

**Alternatives considered**:
- **poetry**: Slower dependency resolution than uv.
- **setuptools only**: Lacks modern lockfile support.

## Strava API Research

### Authentication Flow
- OAuth2 3-legged flow via `https://www.strava.com/oauth/authorize`
- Token exchange at `https://www.strava.com/oauth/token`
- Access tokens expire after 6 hours, refresh via refresh token
- Required scopes: `activity:read_all`, `profile:read_all`
- Token refresh requests do NOT count against rate limits
- stravalib handles the OAuth flow natively

### Rate Limits
- 200 requests per 15 minutes, 2,000 per day (per app)
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Usage`
- 429 response when exceeded; 15-minute windows reset at 0/15/30/45 past hour
- Daily limit resets at midnight UTC

### Key Endpoints for Sync
- `GET /athlete` — authenticated user profile
- `GET /athlete/activities` — paginated activity list (200 per page max)
- `GET /activities/{id}` — detailed activity (includes splits, laps, gear)
- `GET /activities/{id}/streams` — time-series data (HR, power, GPS, etc.)
- `GET /activities/{id}/zones` — heart rate and power zone distributions
- `GET /activities/{id}/laps` — lap data
- `GET /athlete/zones` — athlete's configured zones
- `GET /segments/starred` — starred segments
- `GET /segment_efforts` — efforts on a segment
- `GET /segments/{id}/leaderboard` — segment leaderboard

### Data Available for Analysis (beyond Strava UI)
- Cross-activity zone distributions (aggregate HR/power zones over time)
- Power curve computation from watts stream data
- Long-term pace trend analysis with regression
- Training volume periodization (weekly/monthly aggregation)
- Heart rate drift within activities (cardiac drift analysis)
- Segment effort progression over time
