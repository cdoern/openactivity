# Quickstart: OpenActivity Strava CLI

## Prerequisites

- Python 3.12+
- A Strava account
- A registered Strava API application ([create one here](https://www.strava.com/settings/api))

## Install

```bash
pipx install openactivity
```

Or with pip:

```bash
pip install openactivity
```

## Setup

### 1. Authenticate with Strava

```bash
openactivity strava auth
```

Follow the prompts to enter your Strava API client ID and client secret, then authorize in your browser.

### 2. Sync your data

```bash
openactivity strava sync
```

This pulls all your activities into local storage. First sync may take a few minutes depending on how many activities you have.

### 3. View your activities

```bash
# List recent activities
openactivity strava activities list

# Filter by type and date
openactivity strava activities list --type run --after 2026-01-01

# View a specific activity in detail
openactivity strava activity 12345678
```

## Common Workflows

### Training volume summary

```bash
# Weekly summary for the last 3 months
openactivity strava analyze summary --period weekly --last 90d

# Monthly summary with a bar chart
openactivity strava analyze summary --period monthly --chart bar --output volume.png
```

### Pace trend analysis

```bash
# Running pace over the last 90 days
openactivity strava analyze pace --last 90d --type run
```

### Heart rate zone distribution

```bash
# HR zones across all runs
openactivity strava analyze zones --type run

# Power zones for cycling with a chart
openactivity strava analyze zones --zone-type power --type ride --chart bar --output zones.png
```

### Power curve

```bash
openactivity strava analyze power-curve --last 90d
```

### Export data

```bash
# Export a single activity as GPX
openactivity strava activity 12345678 --export gpx --output ride.gpx

# Bulk export to CSV
openactivity strava activities export --format csv --output activities.csv
```

### Segments

```bash
# List your starred segments
openactivity strava segments list

# View your efforts on a segment
openactivity strava segment 987654 efforts

# Check the leaderboard
openactivity strava segment 987654 leaderboard --friends
```

## Agent / Scripting Usage

All commands support `--json` for machine-readable output:

```bash
# List activities as JSON
openactivity strava activities list --json

# Pipe to jq for processing
openactivity strava activities list --json | jq '.[] | select(.type == "Run")'

# Discover available commands
openactivity strava --help
openactivity strava analyze --help
```

## Configuration

Config file location: `~/.config/openactivity/config.toml`

```toml
[units]
system = "metric"  # or "imperial"

[sync]
detail = true      # fetch streams, laps, zones during sync
```

Override units per-command with `--units imperial`.

## Updating data

Run `openactivity strava sync` periodically to fetch new activities. Sync is incremental — only new or updated data is fetched.

```bash
# Full re-sync (ignores last sync timestamp)
openactivity strava sync --full
```
