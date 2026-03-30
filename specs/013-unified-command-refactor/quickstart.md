# Quickstart: Unified Command Refactoring

**Feature**: 013-unified-command-refactor
**Date**: 2026-03-29

## What's Changing

Commands that were previously only available under `openactivity strava` are now available at the top level and work across all providers.

## Before & After

| Before (still works) | After (new) |
|---|---|
| `openactivity strava analyze pace` | `openactivity analyze pace` |
| `openactivity strava analyze summary` | `openactivity analyze summary` |
| `openactivity strava records list` | `openactivity records list` |
| `openactivity strava records scan` | `openactivity records scan` |
| `openactivity strava predict --distance 5K` | `openactivity predict --distance 5K` |
| `openactivity strava segments list` | `openactivity segments list` |
| `openactivity strava segment 12345 trend` | `openactivity segment 12345 trend` |

## New: `--provider` Filter

All promoted commands accept `--provider` to filter by data source:

```bash
# All providers (default)
openactivity analyze pace

# Only Garmin data
openactivity analyze pace --provider garmin

# Only Strava data
openactivity records list --provider strava
```

## What Stays Under Provider Namespaces

```bash
openactivity strava auth          # Strava OAuth
openactivity strava sync          # Strava data sync
openactivity strava athlete       # Strava profile
openactivity garmin import        # Garmin FIT import
```

## Implementation Approach

1. Move command logic from `cli/strava/analyze.py` → `cli/analyze.py` (extend existing)
2. Move `cli/strava/records.py` → `cli/records.py` (new top-level file)
3. Move `cli/strava/predict.py` → `cli/predict.py` (new top-level file)
4. Move `cli/strava/segments.py` → `cli/segments.py` (new top-level file)
5. Add `--provider` option to each promoted command
6. Add `provider` parameter to `get_activities()` query function
7. Make strava subcommands aliases that set `--provider strava` implicitly
8. Register new top-level apps in `main.py`
