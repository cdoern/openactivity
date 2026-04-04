# Data Model: Unified Command Refactoring

**Feature**: 013-unified-command-refactor
**Date**: 2026-03-29

## Schema Changes

**None.** This feature is a CLI routing refactoring only. No database schema changes are required.

## Query Layer Changes

### `get_activities()` — Add `provider` parameter

The existing `get_activities()` function in `db/queries.py` gains an optional `provider: str | None` parameter. When set, it adds a `WHERE provider = :provider` filter to the query. When `None` (default), it returns activities from all providers (current behavior).

This is the single change that enables `--provider` filtering across all commands — every analysis module already calls `get_activities()`.
