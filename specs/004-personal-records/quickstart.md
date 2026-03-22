# Quickstart: Personal Records Database

## Prerequisites

- openactivity installed and authenticated (`openactivity strava auth`)
- Activities synced with detail streams (`openactivity strava sync --detail`)

## Scan for Personal Records

```bash
# Scan all unscanned activities
openactivity strava records scan

# Force re-scan of all activities
openactivity strava records scan --full
```

## View Current PRs

```bash
# Show all PRs (running + cycling)
openactivity strava records list

# Show only running PRs
openactivity strava records list --type running

# Show only cycling power PRs
openactivity strava records list --type cycling

# JSON output for agents
openactivity strava records list --json
```

## View PR History

```bash
# See 5K progression over time
openactivity strava records history --distance 5K

# See 20-minute power progression
openactivity strava records history --distance 20min

# JSON output
openactivity strava records history --distance 10K --json
```

## Custom Distances

```bash
# Add a custom distance
openactivity strava records add-distance 15K 15000

# Scan to detect PRs for the new distance
openactivity strava records scan

# Remove a custom distance
openactivity strava records remove-distance 15K
```
