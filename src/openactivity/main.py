"""Entry point for the openactivity CLI."""

from __future__ import annotations

from openactivity.cli.config import app as config_app
from openactivity.cli.garmin.app import app as garmin_app
from openactivity.cli.root import app
from openactivity.cli.strava.activities import app as activities_app
from openactivity.cli.strava.activities import show_activity
from openactivity.cli.strava.app import app as strava_app

app.add_typer(strava_app, name="strava")
app.add_typer(garmin_app, name="garmin")
app.add_typer(config_app, name="config")

# Unified provider-agnostic commands at root level
app.add_typer(activities_app, name="activities")
app.command("activity")(show_activity)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
