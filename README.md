# openactivity

CLI tool for pulling, analyzing, and exporting fitness activity data from Strava and Garmin.

openactivity syncs your data to a local SQLite database and lets you query, analyze, and export it offline. It surfaces insights that fitness platforms don't readily show — cross-activity zone distributions, long-term pace trends, power curves, and more.

## Install

```bash
pip install openactivity
```

Or with pipx for isolated installs:

```bash
pipx install openactivity
```

Requires Python 3.12+.

**For Garmin device import (newer watches):** `brew install libmtp` (macOS) or `sudo apt install mtp-tools` (Linux). Not needed if importing from ZIP exports.

## Quick Start

### Strava

```bash
# 1. Register an app at strava.com/settings/api (callback domain: localhost)
# 2. Authenticate
openactivity strava auth
# 3. Sync
openactivity strava sync
```

### Garmin

```bash
# Import directly from a connected Garmin device (USB)
openactivity garmin import --from-device

# Or import from a Garmin Connect bulk export ZIP
openactivity garmin import --from-zip ~/Downloads/export.zip

# Or import from a directory of FIT files
openactivity garmin import --from-directory ~/my-activities/
```

### Browse all your data

```bash
# Unified commands work across all providers
openactivity activities list
openactivity activities list --provider garmin --type Run
openactivity activity 12345678
```

## Commands

```
openactivity
├── activities
│   └── list                    # List activities from all providers
├── activity <ID>               # View activity detail (any provider)
├── config
│   ├── list                    # Show all config values
│   ├── get <key>               # Get a config value
│   └── set <key> <value>       # Set a config value
├── garmin
│   └── import                  # Import from Garmin FIT files
│       ├── --from-device       # Connected Garmin watch (USB)
│       ├── --from-zip PATH     # Garmin Connect bulk export
│       ├── --from-connect      # Garmin Express local folder
│       └── --from-directory    # Custom directory of FIT files
└── strava
    ├── auth                    # OAuth setup
    │   └── revoke              # Remove credentials
    ├── sync                    # Sync data from Strava
    ├── athlete                 # View profile and stats
    ├── activities
    │   ├── list                # List activities with filters
    │   └── export              # Bulk export (CSV/JSON)
    ├── activity <ID>           # View activity detail
    ├── analyze
    │   ├── summary             # Training volume over time
    │   ├── pace                # Pace trend analysis
    │   ├── zones               # HR/power zone distribution
    │   ├── compare             # Compare two time ranges
    │   ├── effort              # Grade-adjusted pace trends
    │   ├── blocks              # Training periodization detection
    │   ├── correlate           # Cross-metric correlation
    │   └── power-curve         # Best power for key durations
    ├── predict                 # Race time predictions
    ├── records
    │   ├── list                # Personal records
    │   ├── history             # PR progression
    │   └── scan                # Scan activities for PRs
    ├── segments
    │   └── list                # List starred segments
    └── segment <ID>
        ├── efforts             # View segment efforts
        ├── trend               # Performance trend analysis
        └── leaderboard         # View leaderboard
```

## Key Features

**Multi-provider**: Import from both Strava (API sync) and Garmin (FIT file import). Unified commands show activities from all providers with `[Strava]`/`[Garmin]` badges. Filter with `--provider`.

**Garmin device support**: Newer watches (Forerunner 265/965, Fenix 7+, Venu 3) are auto-detected via MTP. Older watches mount as USB drives. Also supports bulk export ZIP and custom directories.

**Local-first**: All data stored in SQLite at `~/.local/share/openactivity/openactivity.db`. List, analyze, and export commands never hit the network.

**JSON output**: Every command supports `--json` for scripting and agent consumption.

**Unit support**: Default metric, override with `--units imperial` or set permanently with `openactivity config set units.system imperial`.

**Background sync**: `openactivity strava sync --background` runs sync in the background so you can keep working.

**Export**: Export activities as GPX or CSV. Bulk export with filters.

**Secure credentials**: OAuth tokens stored in your OS keychain (macOS Keychain, Linux Secret Service, Windows Credential Manager).

## Configuration

```bash
# Switch to imperial units
openactivity config set units.system imperial

# View all settings
openactivity config list
```

Config file: `~/.config/openactivity/config.toml`

## Shell Completion

```bash
# Install completions for your shell
openactivity --install-completion
```

## Development

```bash
git clone https://github.com/cdoern/openactivity.git
cd openactivity
make dev        # Install in editable mode with dev deps
make test       # Run tests
make lint       # Run linter
make format     # Format code
```
