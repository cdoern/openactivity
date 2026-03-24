# Research: Cross-Provider Activity Linking

**Feature**: 011-cross-provider-linking
**Date**: 2026-03-24

## R1: Existing Matching Infrastructure

**Decision**: Reuse the existing `detect_duplicate_activities()` and `link_activities()` functions in `queries.py` — they are complete and correct.

**Rationale**: Both functions are fully implemented with proper logic:
- `detect_duplicate_activities()`: ±60s time window, `_types_match()` fuzzy type comparison, ±5% duration tolerance, 0.7 confidence threshold, skips already-linked activities
- `link_activities()`: Creates ActivityLink records with validation, checks for existing links

**Alternatives considered**: Writing new matching logic — rejected because existing code already handles all spec requirements.

## R2: Activity Type Mismatch Between Providers

**Decision**: Extend `_types_match()` to handle the actual type formats in the database.

**Rationale**: Current database shows Strava types as `root='Run'` and Garmin types as `Run`. The existing `_types_match()` handles `run`/`running` etc. but doesn't strip Strava's `root='...'` wrapper. Also, `root='AlpineSki'` vs `Alpine_skiing` needs handling.

**Alternatives considered**: Normalizing types at import time — rejected because it would require re-importing all data and changing the Strava sync logic.

## R3: Auto-Linking Hook Points

**Decision**: Add auto-linking calls after `session.commit()` in both the Garmin importer and Strava sync provider functions.

**Rationale**: The provider-level functions (`import_from_directory()` at line 204, `sync_activities()` at line 243) are the right place because:
1. Activities are already committed to the DB
2. Both CLI and programmatic callers benefit
3. The return dicts/results can be extended with linking stats

**Alternatives considered**:
- Hooking in CLI layer only — rejected because programmatic callers wouldn't get auto-linking
- Hooking during activity creation (before commit) — rejected because the session needs committed IDs for linking

## R4: Bulk Link Command Location

**Decision**: Add `openactivity activities link` as a subcommand of the existing `activities` typer app in `cli/strava/activities.py` (which is already mounted at root level as `openactivity activities`).

**Rationale**: The `activities` app is already registered at the root level in `main.py` and handles cross-provider activity listing. Linking is a cross-provider operation that belongs at the same level.

**Alternatives considered**:
- New top-level command `openactivity link` — rejected because linking is an operation on activities, not a separate concept
- Provider-specific commands — rejected because linking is inherently cross-provider

## R5: Primary Provider Default

**Decision**: Default primary provider to "strava" for linked activities.

**Rationale**: Strava typically has richer metadata: GPS streams, segment efforts, social data, detailed splits. When displaying a linked activity, the primary provider's data is preferred.

**Alternatives considered**: User-configurable default — rejected as premature; can be added later if needed.

## R6: Strava Type Format Parsing

**Decision**: Add type normalization that strips Strava's `root='...'` format before comparison.

**Rationale**: Strava stores types as `root='Run'`, `root='AlpineSki'` etc. in the database. The `_types_match()` function needs to extract the inner value before comparing. Also need to map `AlpineSki` → `alpine_skiing` for cross-provider matching.

**Alternatives considered**: Changing Strava sync to store clean types — would require re-sync of all data.
