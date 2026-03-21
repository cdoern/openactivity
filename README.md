# openactivity

CLI tool for pulling, analyzing, and exporting fitness activity data from providers like Strava.

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

## Quick Start

### 1. Register a Strava API app

Go to [strava.com/settings/api](https://www.strava.com/settings/api) and create an application. Set the Authorization Callback Domain to `localhost`.

### 2. Authenticate

```bash
openactivity strava auth
```

Enter your Client ID and Client Secret when prompted, then authorize in your browser.

### 3. Sync your data

```bash
openactivity strava sync
```

First sync fetches all activities. Subsequent syncs are incremental.

### 4. Explore

```bash
openactivity strava activities list
openactivity strava activity 12345678
openactivity strava athlete
```

## Commands

```
openactivity
├── config
│   ├── list                    # Show all config values
│   ├── get <key>               # Get a config value
│   └── set <key> <value>       # Set a config value
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
    │   └── power-curve         # Best power for key durations
    ├── segments
    │   └── list                # List starred segments
    └── segment <ID>
        ├── efforts             # View segment efforts
        └── leaderboard         # View leaderboard
```

## Key Features

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
