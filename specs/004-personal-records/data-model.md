# Data Model: Personal Records Database

**Branch**: `004-personal-records` | **Date**: 2026-03-21

## Overview

Two new persisted entities are added to the existing database. One existing entity is modified with a new column.

## New Entities

### PersonalRecord

A best effort at a specific distance or power duration.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| id | integer (PK) | No | Auto-incrementing primary key |
| record_type | string | No | "distance" or "power" — distinguishes running PRs from cycling PRs |
| distance_type | string | No | Canonical label (e.g., "1mi", "5K", "10K", "half", "marathon", "5s", "1min", "5min", "20min", "60min", or custom like "15K") |
| value | float | No | Time in seconds (for distance PRs) or watts (for power PRs) |
| pace | float | Yes | Seconds per meter (for distance PRs), null for power PRs |
| activity_id | integer | No | Foreign key to activities table |
| activity_name | string | Yes | Denormalized activity name for display convenience |
| achieved_date | datetime | No | Date the PR was set (from activity start_date) |
| is_current | boolean | No | True if this is the current best record for this distance_type |
| distance_meters | float | Yes | Target distance in meters (for distance PRs), null for power PRs |
| duration_seconds | integer | Yes | Target duration in seconds (for power PRs), null for distance PRs |
| created_at | datetime | No | Timestamp when record was created |

**Indexes**:
- `ix_pr_distance_type` on (distance_type) — fast lookup by distance
- `ix_pr_current` on (is_current, distance_type) — fast current PR queries
- `ix_pr_activity` on (activity_id) — fast lookup by activity

**Constraints**:
- At most one record per distance_type can have `is_current = TRUE`
- activity_id references Activity.id

### CustomDistance

A user-defined distance for PR tracking.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| id | integer (PK) | No | Auto-incrementing primary key |
| label | string (unique) | No | Display label (e.g., "15K", "50K") |
| distance_meters | float | No | Distance in meters |
| created_at | datetime | No | Timestamp when distance was added |

**Constraints**:
- Label must be unique
- Label must not conflict with standard distance labels

## Modified Entity

### Activity (existing)

| New Field | Type | Nullable | Default | Description |
|-----------|------|----------|---------|-------------|
| pr_scanned | boolean | No | False | Whether this activity has been scanned for PRs |

## Standard Distances (constants, not in DB)

### Running Distances

| Label | Distance (meters) |
|-------|-------------------|
| 1mi | 1609.344 |
| 5K | 5000.0 |
| 10K | 10000.0 |
| half | 21097.5 |
| marathon | 42195.0 |

### Cycling Power Durations

| Label | Duration (seconds) |
|-------|-------------------|
| 5s | 5 |
| 1min | 60 |
| 5min | 300 |
| 20min | 1200 |
| 60min | 3600 |

## Relationships

```
Activity (existing) --[1:many]--> PersonalRecord (activity_id FK)
Activity (existing) --[1:many]--> ActivityStream (existing, used for scanning)
CustomDistance --[label matches]--> PersonalRecord.distance_type (logical, not FK)
```

## State Transitions

### PersonalRecord.is_current

```
New PR detected for distance_type:
  1. Find existing record WHERE distance_type = X AND is_current = TRUE
  2. If exists AND new value is better (lower time or higher watts):
     a. Set existing.is_current = FALSE
     b. Insert new record with is_current = TRUE
  3. If not exists:
     a. Insert new record with is_current = TRUE
  4. If exists AND new value is NOT better:
     a. Do nothing (record not inserted)
```
