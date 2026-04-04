# Research: Unified Command Refactoring

**Feature**: 013-unified-command-refactor
**Date**: 2026-03-29

## Research Topics

### 1. Typer Command Aliasing Pattern

**Decision**: Use `add_typer()` to register the same Typer app at multiple levels — once at root and once under `strava`. The `strava` registration can use a callback that sets a global `provider` state.

**Rationale**: Typer supports registering the same app instance in multiple parent apps. This avoids code duplication entirely. The existing `get_global_state()` pattern already passes state from parent to child commands.

**Alternatives considered**:
- Thin wrapper functions that call the real functions with `--provider strava`: More code, harder to maintain.
- Symlink-style approach with separate Typer apps: Duplicate registration code.
- Remove strava commands entirely: Breaks backwards compatibility, violates constitution.

### 2. Provider Filtering in Analysis/Query Layer

**Decision**: Add an optional `provider` parameter to the existing `get_activities()` query function. Pass it through from the CLI `--provider` option. When `None`, query all providers (current behavior). When set, filter by `Activity.provider == provider`.

**Rationale**: The query layer already supports filtering by type, date range, etc. Adding provider is a one-line filter. The analysis modules call `get_activities()` and will automatically respect the filter without changes.

**Alternatives considered**:
- Filter at the CLI layer after querying: Wasteful — queries all data then discards.
- Separate query functions per provider: Unnecessary duplication.

### 3. Handling the Existing Top-Level `analyze` App

**Decision**: The top-level `cli/analyze.py` already has a `fitness` command. Move the strava analyze commands (summary, pace, zones, power-curve, compare) into this same file, adding `--provider` to each. The strava analyze app then becomes an alias.

**Rationale**: Consolidating into one file keeps things simple. The fitness command already works provider-agnostically. The strava commands just need the provider filter added.

**Alternatives considered**:
- Keep analyze.py small and import from strava/analyze.py: Creates confusing import direction.
- Split into cli/analyze/ package with submodules: Over-engineering for 6 commands.

### 4. Records Scanner Provider Awareness

**Decision**: The records scanner (`scan_all_activities`) already queries all activities regardless of provider. It uses `Activity.pr_scanned` flag which is provider-agnostic. The `--provider` filter only needs to apply to `records list` (display) and optionally `records scan` (to scan only one provider's activities).

**Rationale**: PRs should be detected across all providers by default. A user's 5K PR is their 5K PR regardless of whether Strava or Garmin recorded it.

**Alternatives considered**:
- Only scan activities from one provider at a time: Misses cross-provider PRs.

### 5. Backwards Compatibility Strategy

**Decision**: Keep the strava subcommands working by registering the top-level Typer apps under both the root and the strava app. The strava app callback sets `provider=strava` in global state before any subcommand runs.

**Rationale**: Constitution Principle V requires deprecation cycle for breaking changes. Users and scripts may depend on `openactivity strava analyze pace`. Making it an alias costs nothing and preserves compatibility.

**Alternatives considered**:
- Print deprecation warning on strava paths: Annoying for users, not needed yet since this is a promotion not a removal.
- Remove strava paths immediately: Violates constitution.

### 6. Duplicate `strava activities` / `strava activity` Commands

**Decision**: The `strava activities` and `strava activity` commands already point to the same functions as the top-level `activities` and `activity` commands (both import from `strava/activities.py`). Keep them as-is — they're already aliases by implementation.

**Rationale**: No change needed. The code already shares the same function references.
