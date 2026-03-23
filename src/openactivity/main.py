"""Entry point for the openactivity CLI."""

from __future__ import annotations

from openactivity.cli.config import app as config_app
from openactivity.cli.garmin.app import app as garmin_app
from openactivity.cli.root import app
from openactivity.cli.strava.app import app as strava_app

app.add_typer(strava_app, name="strava")
app.add_typer(garmin_app, name="garmin")
app.add_typer(config_app, name="config")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
