# CLI Command Contract: Unified Command Tree

**Feature**: 013-unified-command-refactor
**Date**: 2026-03-29

## New Top-Level Command Tree

```
openactivity
├── activity <ID>                          # EXISTING (unchanged)
├── activities list|search                 # EXISTING (unchanged)
├── analyze                                # EXISTING (fitness) + PROMOTED commands
│   ├── fitness [--last] [--type] [--chart] [--provider]
│   ├── summary [--last] [--type] [--provider]        # FROM strava analyze
│   ├── pace [--last] [--type] [--provider]            # FROM strava analyze
│   ├── zones [--last] [--type] [--provider]           # FROM strava analyze
│   ├── power-curve [--last] [--provider]              # FROM strava analyze
│   ├── compare --range1 --range2 [--type] [--provider] # FROM strava analyze
│   ├── correlate --x --y [--last] [--provider]        # FROM strava analyze
│   ├── effort [--last] [--type] [--provider]          # FROM strava analyze
│   ├── blocks [--last] [--type] [--provider]          # FROM strava analyze
│   ├── drift [--last] [--type] [--provider]           # FROM strava analyze
│   └── risk [--last] [--provider]                     # FROM strava analyze
├── records                                # PROMOTED from strava records
│   ├── scan [--full] [--provider]
│   ├── list [--type] [--provider]
│   ├── history --distance [--provider]
│   ├── add-distance <label> --miles|--km|--meters
│   └── remove-distance <label>
├── predict --distance [--race-date] [--provider]  # PROMOTED from strava predict
├── segments list [--provider]             # PROMOTED from strava segments
├── segment <ID>                           # PROMOTED from strava segment
│   ├── efforts [--provider]
│   ├── leaderboard
│   └── trend [--provider]
├── config list|get|set                    # EXISTING (unchanged)
├── strava                                 # PROVIDER-SPECIFIC (kept)
│   ├── auth [revoke]
│   ├── sync [--full] [--detail]
│   ├── athlete
│   ├── analyze ...                        # ALIAS → openactivity analyze --provider strava
│   ├── records ...                        # ALIAS → openactivity records --provider strava
│   ├── predict ...                        # ALIAS → openactivity predict --provider strava
│   ├── segments ...                       # ALIAS → openactivity segments --provider strava
│   ├── segment ...                        # ALIAS → openactivity segment --provider strava
│   ├── activities ...                     # ALIAS → openactivity activities (existing)
│   └── activity ...                       # ALIAS → openactivity activity (existing)
└── garmin                                 # PROVIDER-SPECIFIC (kept)
    └── import --from-device|--from-connect|--from-zip|--from-directory
```

## `--provider` Flag Contract

- **Flag name**: `--provider`
- **Type**: `str | None`
- **Default**: `None` (all providers)
- **Accepted values**: `strava`, `garmin`
- **Behavior when None**: Include data from all providers
- **Behavior when set**: Filter to only that provider's data
- **Applied at**: Query layer (`get_activities()` and similar query functions)
- **Present on**: All promoted commands (analyze, records, predict, segments, segment)
- **NOT present on**: Provider-specific commands (auth, sync, import), config, add-distance, remove-distance
