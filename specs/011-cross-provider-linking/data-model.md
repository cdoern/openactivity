# Data Model: Cross-Provider Activity Linking

**Feature**: 011-cross-provider-linking
**Date**: 2026-03-24

## Existing Entities (No Changes)

### Activity

Already has `provider` (String, default "strava") and `provider_id` fields. No schema changes needed.

### ActivityLink

Already exists with correct schema:

| Field | Type | Constraints |
|-------|------|-------------|
| id | Integer | Primary key, autoincrement |
| strava_activity_id | Integer | FK → activities.id, nullable, cascade delete |
| garmin_activity_id | Integer | FK → activities.id, nullable, cascade delete |
| primary_provider | String | Not null |
| match_confidence | Float | 0.0–1.0, not null |
| created_at | DateTime | Default CURRENT_TIMESTAMP |

**Check constraint**: At least one activity ID must be non-null.

## Data Flow

### Bulk Linking Flow

```
User runs `activities link`
  → Query all activities where provider="strava" and no existing ActivityLink
  → For each, call detect_duplicate_activities() to find garmin matches
  → For each match above 0.7 confidence, call link_activities()
  → Return stats: {scanned, matched, linked, skipped, ambiguous}
```

### Auto-Linking Flow (Import/Sync)

```
After garmin import commits new activities:
  → Query newly imported activities (provider="garmin")
  → For each, call detect_duplicate_activities() to find strava matches
  → Link best match if confidence >= 0.7
  → Append linking stats to import result

After strava sync commits new activities:
  → Query newly synced activities (provider="strava", from this sync batch)
  → For each, call detect_duplicate_activities() to find garmin matches
  → Link best match if confidence >= 0.7
  → Append linking stats to sync result
```

### Unlink Flow

```
User runs `activities link --unlink <activity_id>`
  → Find ActivityLink where strava_activity_id=id OR garmin_activity_id=id
  → Delete the link record
  → Both activities remain in DB as separate entries
```

## Type Normalization Map

The `_types_match()` function needs these additional mappings:

| Strava Format | Garmin Format | Normalized |
|---------------|---------------|------------|
| `root='Run'` | `Run` | run |
| `root='AlpineSki'` | `Alpine_skiing` | alpine_ski |
| `root='Workout'` | `Strength` | (no match — different activities) |

**Normalization steps**:
1. Strip `root='...'` wrapper if present → extract inner value
2. Convert to lowercase
3. Replace underscores with nothing for comparison
4. Check against type group sets (run_types, ride_types, etc.)
