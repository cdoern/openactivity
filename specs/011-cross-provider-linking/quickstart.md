# Quickstart: Cross-Provider Activity Linking

## What This Feature Does

Automatically detects and links duplicate activities that were recorded by both Strava and Garmin. After linking, the unified activity list shows matched activities with a `[Strava+Garmin]` badge instead of showing them as separate entries.

## Quick Test

```bash
# 1. Ensure you have activities from both providers
openactivity activities list --provider strava --limit 5
openactivity activities list --provider garmin --limit 5

# 2. Preview what will be linked (no changes made)
openactivity activities link --dry-run

# 3. Link matching activities
openactivity activities link

# 4. Verify linked activities show combined badge
openactivity activities list
# Activities recorded on both platforms now show [Strava+Garmin]

# 5. If a link is wrong, remove it
openactivity activities link --unlink <activity_id>
```

## Auto-Linking

After the initial bulk link, new activities are automatically linked:

```bash
# Garmin import auto-links against existing Strava activities
openactivity garmin import --from-device

# Strava sync auto-links against existing Garmin activities
openactivity strava sync
```

Both commands now show linking stats in their output summary.

## Key Files

| File | Purpose |
|------|---------|
| `src/openactivity/db/queries.py` | Core matching + linking logic |
| `src/openactivity/cli/strava/activities.py` | `activities link` command |
| `src/openactivity/providers/garmin/importer.py` | Auto-link hook after import |
| `src/openactivity/providers/strava/sync.py` | Auto-link hook after sync |
