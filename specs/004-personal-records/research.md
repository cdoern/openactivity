# Research: Personal Records Database

**Branch**: `004-personal-records` | **Date**: 2026-03-21

## Research Summary

This feature requires no new external dependencies. Key research covers the sliding window algorithm for distance-based PR detection and the data model for persisting records with history.

## Decisions

### 1. Sliding Window Algorithm for Distance PRs

**Decision**: Two-pointer sliding window over the cumulative distance stream. Find all (start, end) index pairs where `distance[end] - distance[start] >= target_distance`, then pick the pair with minimum time delta using the time stream.

**Rationale**: The distance stream is monotonically increasing (cumulative). A two-pointer approach is O(n) per target distance per activity, which is optimal. No need for binary search since we process sequentially.

**Alternatives considered**:
- Binary search for each start index — O(n log n), marginally more complex with no practical speed gain for typical stream sizes (1000-5000 points).
- Brute force all pairs — O(n²), too slow for long activities.

### 2. Power Duration Best Effort Detection

**Decision**: Reuse the sliding window approach from the existing `analysis/power.py` module. The existing `_find_best_power` function already computes best average power for a given duration using a sliding window over the watts stream.

**Rationale**: The power curve analysis already solves this problem. Extract and reuse the algorithm rather than reimplementing. The difference is that records.py persists the results rather than computing on the fly.

**Alternatives considered**:
- Import and call `compute_power_curve` directly — too tightly coupled; it returns formatted dicts, not raw data suitable for persistence.
- Duplicate the algorithm — violates DRY. Better to extract a shared utility.

### 3. Record History Model

**Decision**: Use a single `PersonalRecord` table with an `is_current` boolean flag. All records for a distance are kept; only one per distance is marked current. History is queried by filtering on distance type and ordering by date.

**Rationale**: Simpler than a linked list (previous_record_id). Querying current PRs is a simple `WHERE is_current = TRUE`. History is `WHERE distance_type = X ORDER BY date`. No recursive queries needed.

**Alternatives considered**:
- Linked list via `previous_record_id` foreign key — adds complexity for traversal, harder to query "all records for 5K" without recursion.
- Separate `PRHistory` table — unnecessary table proliferation for a simple append-only pattern.

### 4. Incremental Scan Tracking

**Decision**: Add a `pr_scanned` boolean column to the existing `Activity` model. After scanning an activity, mark it as scanned. Subsequent scans query `WHERE pr_scanned = FALSE`.

**Rationale**: Simple, fast, and avoids a separate tracking table. The column is indexed implicitly through the activity queries. A full re-scan can reset all flags via `UPDATE activities SET pr_scanned = FALSE`.

**Alternatives considered**:
- Separate `ScanState` entry for PR scanning — adds complexity for a simple boolean state.
- Track last-scanned timestamp — doesn't handle activities synced out of order.

### 5. Custom Distance Storage

**Decision**: Separate `CustomDistance` table with label and distance_meters columns. Standard distances are hardcoded constants in the analysis module. Custom distances are queried at scan time and merged with standard distances.

**Rationale**: Standard distances should not be in the database (they're fixed). Custom distances need persistence. Keeping them separate prevents users from accidentally modifying standard distances.

**Alternatives considered**:
- Store all distances (standard + custom) in the DB — risks users deleting standard distances.
- Store custom distances in config file — inconsistent with the DB-first approach for all other data.

### 6. Stream Data Format

**Decision**: Activity streams store data as JSON-encoded bytes in a `LargeBinary` column. The distance stream contains cumulative distance values in meters. The time stream contains cumulative elapsed seconds. These are deserialized with `json.loads()` at scan time.

**Rationale**: This is the existing format in the codebase (see `ActivityStream.data` field). No changes needed to stream storage.

**Alternatives considered**: None — must use the existing format.
