# openactivity Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-13

## Active Technologies
- Python 3.12+ + yper (CLI), rich (terminal output), sqlalchemy (ORM), stravalib (Strava API), keyring (credentials), matplotlib (charts), gpxpy (GPX export), httpx (HTTP client) (001-strava-cli)
- SQLite (embedded, WAL mode) at `~/.local/share/openactivity/openactivity.db` (001-strava-cli)

- Go 1.22+ + spf13/cobra (CLI), spf13/viper (config), gorm.io/driver/sqlite (storage), golang.org/x/oauth2 (auth), zalando/go-keyring (credentials), jedib0t/go-pretty (tables), go-echarts/go-echarts (charts), twpayne/go-gpx (GPX export) (001-strava-cli)

## Project Structure

```text
src/
tests/
```

## Commands

# Add commands for Go 1.22+

## Code Style

Go 1.22+: Follow standard conventions

## Recent Changes
- 001-strava-cli: Added Python 3.12+ + yper (CLI), rich (terminal output), sqlalchemy (ORM), stravalib (Strava API), keyring (credentials), matplotlib (charts), gpxpy (GPX export), httpx (HTTP client)

- 001-strava-cli: Added Go 1.22+ + spf13/cobra (CLI), spf13/viper (config), gorm.io/driver/sqlite (storage), golang.org/x/oauth2 (auth), zalando/go-keyring (credentials), jedib0t/go-pretty (tables), go-echarts/go-echarts (charts), twpayne/go-gpx (GPX export)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
